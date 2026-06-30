#!/usr/bin/env python3
"""
cleanup_hyperdeck.py

Guarded Python implementation of HyperDeck cleanup. It supports separate local
and remote cleanup modes, dry-run execution, and targeted slot selection so it
can be validated safely before replacing the scheduled bash cleanup path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ftplib
import os
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pipeline_config import CONFIG_PATH, load_config


SCRIPT_NAME = "cleanup_hyperdeck.py"
FTP_TIMEOUT_SECONDS = 10
VALID_SLOTS = {"sd1", "sd2", "1", "2"}


@dataclass(frozen=True)
class RemoteTarget:
    deck_name: str
    ip: str
    slot: str

def timestamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_log_parent(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)


def log(message: str, log_file: Path) -> None:
    line = f"[{timestamp()}] [{SCRIPT_NAME}] {message}"
    print(line, flush=True)
    ensure_log_parent(log_file)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def hostname_alias() -> str:
    return os.environ.get("HYPERDECK_HOST_ALIAS", socket.gethostname())


def tail_lines(path: Path, count: int) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-count:])


def send_email(log_file: Path, recipients: tuple[str, ...], subject: str, line_count: int) -> None:
    mail_binary = shutil.which("mail")
    if not mail_binary:
        raise RuntimeError("mail command not found in PATH")

    body = tail_lines(log_file, line_count)
    subprocess.run(
        [mail_binary, "-s", subject, *recipients],
        input=body,
        text=True,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    defaults = load_config()
    parser = argparse.ArgumentParser(
        description="Clean local HyperDeck downloads and/or remote HyperDeck slots.",
    )
    parser.add_argument(
        "--local-dir",
        default=str(defaults.downloads_dir),
        help="Local HyperDeck download directory",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Path to the shared HyperDeck pipeline config",
    )
    parser.add_argument(
        "--log-file",
        default=str(defaults.log_file),
        help="Shared log file path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show cleanup actions without deleting anything",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only perform local cleanup",
    )
    parser.add_argument(
        "--remote-only",
        action="store_true",
        help="Only perform remote cleanup",
    )
    parser.add_argument(
        "--slot",
        action="append",
        default=[],
        metavar="DECK:SLOT",
        help="Limit remote cleanup to one or more slots, e.g. HD1:sd1",
    )
    parser.add_argument(
        "--confirm-remote",
        action="store_true",
        help="Required for real remote deletion when not using --dry-run",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip the cleanup summary email",
    )
    parser.add_argument(
        "--email-to",
        nargs="+",
        default=list(defaults.email_recipients),
        help="Email recipients for the cleanup summary",
    )
    return parser.parse_args()


def validate_mode_args(args: argparse.Namespace) -> None:
    if args.local_only and args.remote_only:
        raise SystemExit("Cannot combine --local-only and --remote-only")
    if args.slot and args.local_only:
        raise SystemExit("--slot cannot be combined with --local-only")
    if not args.dry_run and not args.local_only and not args.confirm_remote:
        raise SystemExit("Real remote cleanup requires --confirm-remote")
    if not args.dry_run and args.remote_only and not args.confirm_remote:
        raise SystemExit("Real remote cleanup requires --confirm-remote")


def remote_targets_from_config(config_path: Path) -> list[RemoteTarget]:
    config = load_config(config_path)
    targets: list[RemoteTarget] = []
    for deck in config.hyperdecks:
        for slot in deck.volumes:
            if slot in VALID_SLOTS:
                targets.append(RemoteTarget(deck.name, deck.ip, slot))
    return targets


def parse_slot_filters(raw_filters: list[str], available_targets: list[RemoteTarget]) -> list[RemoteTarget]:
    if not raw_filters:
        return list(available_targets)

    by_key = {(target.deck_name, target.slot): target for target in available_targets}
    selected: list[RemoteTarget] = []
    for raw in raw_filters:
        deck_name, sep, slot = raw.partition(":")
        if not sep:
            raise SystemExit(f"Invalid --slot value '{raw}'. Expected DECK:SLOT.")
        if slot not in VALID_SLOTS:
            raise SystemExit(f"Invalid slot '{slot}' in --slot value '{raw}'.")
        target = by_key.get((deck_name, slot))
        if target is None:
            raise SystemExit(f"Unknown remote target '{raw}'.")
        selected.append(target)
    return selected


def ftp_connect(ip: str) -> ftplib.FTP:
    ftp = ftplib.FTP(timeout=FTP_TIMEOUT_SECONDS)
    ftp.connect(ip, 21)
    ftp.login()
    return ftp


def list_remote_mp4s(ftp: ftplib.FTP, slot: str) -> list[str]:
    try:
        entries = ftp.nlst(slot)
    except ftplib.all_errors:
        return []

    names: list[str] = []
    for entry in entries:
        cleaned = entry.rstrip("/").split("/")[-1]
        if cleaned.lower().endswith(".mp4"):
            names.append(cleaned)
    return sorted(set(names))


def cleanup_local(local_dir: Path, dry_run: bool, log_file: Path) -> None:
    log(f"📂 Checking for local MP4 files in {local_dir}...", log_file)
    mp4_files = sorted(path for path in local_dir.rglob("*.mp4") if path.is_file()) if local_dir.exists() else []
    if not mp4_files:
        log("✅ No local MP4 files found — nothing to delete.", log_file)
    else:
        if dry_run:
            for path in mp4_files:
                log(f"🧪 (Dry Run) Would delete local MP4: {path}", log_file)
        else:
            for path in mp4_files:
                path.unlink()
            log(f"🗑️ Deleted {len(mp4_files)} local MP4 file(s).", log_file)

    log("🧹 Removing broken symlinks...", log_file)
    broken_symlinks = sorted(path for path in local_dir.rglob("*") if path.is_symlink() and not path.exists()) if local_dir.exists() else []
    if not broken_symlinks:
        log("✅ No broken symlinks found.", log_file)
        return

    if dry_run:
        for path in broken_symlinks:
            log(f"🧪 (Dry Run) Would delete broken symlink: {path}", log_file)
        return

    for path in broken_symlinks:
        path.unlink()
    log(f"🗑️ Deleted {len(broken_symlinks)} broken symlink(s).", log_file)


def cleanup_remote(target: RemoteTarget, dry_run: bool, log_file: Path) -> None:
    log(f"🌐 Checking remote files on {target.deck_name} ({target.ip}), slot: {target.slot}...", log_file)
    try:
        with ftp_connect(target.ip) as ftp:
            remote_files = list_remote_mp4s(ftp, target.slot)
            if not remote_files:
                log(f"✅ No .mp4 files to delete in {target.slot} on {target.deck_name} ({target.ip}).", log_file)
                return

            if dry_run:
                for name in remote_files:
                    log(
                        f"🧪 (Dry Run) Would delete remote MP4 on {target.deck_name} "
                        f"({target.ip}), slot {target.slot}: {name}",
                        log_file,
                    )
                return

            log(f"🗑️ Deleting remote MP4 files from {target.slot} on {target.deck_name} ({target.ip})...", log_file)
            for name in remote_files:
                ftp.delete(f"{target.slot}/{name}")
            log(f"✅ Remote deletion complete on {target.deck_name} ({target.ip}), slot: {target.slot}.", log_file)
    except (OSError, ftplib.all_errors) as exc:
        log(
            f"⚠️ Could not access slot '{target.slot}' on {target.deck_name} ({target.ip}) "
            f"within {FTP_TIMEOUT_SECONDS}s — skipping. ({exc})",
            log_file,
        )


def main() -> int:
    args = parse_args()
    validate_mode_args(args)

    config_path = Path(args.config).expanduser()
    config = load_config(config_path)
    local_dir = Path(args.local_dir).expanduser()
    log_file = Path(args.log_file).expanduser()
    remote_targets = parse_slot_filters(args.slot, remote_targets_from_config(config_path))

    ensure_log_parent(log_file)
    log_file.touch(exist_ok=True)

    log("🧹 Starting cleanup process...", log_file)

    if not args.remote_only:
        cleanup_local(local_dir, args.dry_run, log_file)

    if not args.local_only:
        for target in remote_targets:
            cleanup_remote(target, args.dry_run, log_file)

    log("🏁 Cleanup process complete.", log_file)

    if args.no_email:
        log("⏭️ Skipping cleanup email summary.", log_file)
    else:
        recipients = tuple(args.email_to)
        subject = f"[{hostname_alias()}] 🧹 HyperDeck Cleanup Summary – {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        log(f"📧 Sending cleanup email summary to {' '.join(recipients)}...", log_file)
        try:
            send_email(log_file, recipients, subject, config.mail_tail_lines)
        except Exception as exc:  # noqa: BLE001
            log(f"❌ Cleanup email step failed: {exc}", log_file)
            return 1

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
