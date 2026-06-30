#!/usr/bin/env python3
"""
master_sync_upload.py

Production-oriented Python orchestration for the HyperDeck pipeline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from pipeline_config import CONFIG_PATH, load_config


SCRIPT_NAME = "master_sync_upload.py"
DEFAULT_SYNC_SCRIPT = Path(__file__).resolve().parent / "hyperdeck_sync.py"
DEFAULT_RENAME_SCRIPT = Path(__file__).resolve().parent / "rename_files.py"
DEFAULT_UPLOAD_SCRIPT = Path(__file__).resolve().parent / "copy_to_gdrive.py"
DEFAULT_HYPERDECKS = ("HD1", "HD2")


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


def join_by_comma(values: list[str]) -> str:
    return ", ".join(values)


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


def run_command(command: list[str], log_file: Path) -> int:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)

    return process.wait()


def script_command(script_path: Path, *args: str) -> list[str]:
    if script_path.suffix == ".py":
        return [sys.executable, str(script_path), *args]
    return [str(script_path), *args]


def parse_args() -> argparse.Namespace:
    defaults = load_config()
    parser = argparse.ArgumentParser(
        description="Run HyperDeck sync, rename, upload, and email summary via Python orchestration.",
    )
    parser.add_argument(
        "--dest",
        default=str(defaults.downloads_dir),
        help="Destination root for synced downloads",
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
        "--sync-script",
        default=str(DEFAULT_SYNC_SCRIPT),
        help="Path to hyperdeck_sync.py",
    )
    parser.add_argument(
        "--rename-script",
        default=str(DEFAULT_RENAME_SCRIPT),
        help="Path to the rename step implementation",
    )
    parser.add_argument(
        "--upload-script",
        default=str(DEFAULT_UPLOAD_SCRIPT),
        help="Path to the upload step implementation",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip the email summary",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip the Google Drive upload stage",
    )
    parser.add_argument(
        "--upload-dry-run",
        action="store_true",
        help="Run the upload stage in dry-run mode",
    )
    parser.add_argument(
        "--sync-dry-run",
        action="store_true",
        help="Run hyperdeck_sync.py in dry-run mode",
    )
    parser.add_argument(
        "--sync-while-recording",
        action="store_true",
        help="Allow sync while a HyperDeck is actively recording",
    )
    parser.add_argument(
        "--email-to",
        nargs="+",
        default=list(defaults.email_recipients),
        help="Email recipients for the summary",
    )
    parser.add_argument(
        "--hyperdecks",
        nargs="+",
        default=list(DEFAULT_HYPERDECKS),
        help="HyperDeck names to process in order",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config).expanduser())
    destination = Path(args.dest).expanduser()
    log_file = Path(args.log_file).expanduser()
    sync_script = Path(args.sync_script).expanduser()
    rename_script = Path(args.rename_script).expanduser()
    upload_script = Path(args.upload_script).expanduser()

    destination.mkdir(parents=True, exist_ok=True)
    ensure_log_parent(log_file)
    log_file.touch(exist_ok=True)

    log("📝 Starting Python master sync process...", log_file)
    log(f"📁 Destination: {destination}", log_file)
    log(f"☁️ Upload enabled: {str(not args.no_upload).lower()}", log_file)
    log(f"📧 Email enabled: {str(not args.no_email).lower()}", log_file)

    successful_syncs: list[str] = []
    failed_syncs: list[str] = []

    for deck_name in args.hyperdecks:
        log(f"🔁 Starting Python sync for {deck_name}...", log_file)
        sync_command = [
            sys.executable,
            str(sync_script),
            deck_name,
            str(destination),
            "--config",
            str(Path(args.config).expanduser()),
            "--log-file",
            str(log_file),
        ]
        if args.sync_dry_run:
            sync_command.append("--dry-run")
        if args.sync_while_recording:
            sync_command.append("--sync-while-recording")

        exit_code = run_command(sync_command, log_file)
        if exit_code == 0:
            log(f"✅ Python sync complete for {deck_name}.", log_file)
            successful_syncs.append(deck_name)
        else:
            log(f"❌ Python sync failed for {deck_name}. Continuing with remaining HyperDecks.", log_file)
            failed_syncs.append(deck_name)

    if failed_syncs:
        log(
            f"⚠️ Completed with sync failures for: {join_by_comma(failed_syncs)}. "
            "Skipping rename and upload steps.",
            log_file,
        )
    elif successful_syncs:
        log("✍️ Renaming downloaded files...", log_file)
        rename_exit = run_command(
            script_command(
                rename_script,
                "--config",
                str(Path(args.config).expanduser()),
                "--log-file",
                str(log_file),
                str(destination),
            ),
            log_file,
        )
        if rename_exit != 0:
            log("❌ Rename step failed.", log_file)
            return rename_exit
        log("✅ Renaming complete.", log_file)

        if args.no_upload:
            log("⏭️ Skipping Google Drive upload.", log_file)
        else:
            log("☁️ Uploading files to Google Drive...", log_file)
            upload_command = script_command(
                upload_script,
                "--config",
                str(Path(args.config).expanduser()),
                "--log-file",
                str(log_file),
                str(destination),
            )
            if args.upload_dry_run:
                upload_command.append("--dry-run")
            upload_exit = run_command(upload_command, log_file)
            if upload_exit != 0:
                log("❌ Upload step failed.", log_file)
                return upload_exit
            log("✅ Upload to Google Drive complete.", log_file)
    else:
        log("⚠️ No HyperDeck syncs succeeded. Skipping rename and upload steps.", log_file)

    if args.no_email:
        log("⏭️ Skipping email summary.", log_file)
    else:
        recipients = tuple(args.email_to)
        subject = f"[{hostname_alias()}] 📦 HyperDeck Upload Summary – {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        log(f"📧 Sending email summary to {' '.join(recipients)}...", log_file)
        try:
            send_email(log_file, recipients, subject, config.mail_tail_lines)
        except Exception as exc:  # noqa: BLE001
            log(f"❌ Email step failed: {exc}", log_file)
            return 1

    log("🏁 Python master sync process complete.", log_file)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n")

    if failed_syncs:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
