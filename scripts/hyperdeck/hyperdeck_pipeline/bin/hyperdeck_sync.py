#!/usr/bin/env python3
"""
hyperdeck_sync.py

Python implementation of HyperDeck file sync using only the standard library.
This is the first production-oriented step beyond the older inventory-only
prototype so it can be tested against live HyperDecks without relying on lftp.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ftplib
import os
import re
import socket
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pipeline_config import CONFIG_PATH, HyperDeckConfig, ServiceWindow, load_config


SCRIPT_NAME = "hyperdeck_sync.py"
FTP_PORT = 21
TRANSPORT_PORT = 9993
SOCKET_TIMEOUT_SECONDS = 5
SLOT_DISCOVERY_ATTEMPTS = 3
SLOT_DISCOVERY_SLEEP_SECONDS = 5
VALID_SLOTS = {"1", "2", "sd1", "sd2"}
DOWNLOADED_FILE_MODE = 0o644
HD1_FILENAME_RE = re.compile(r"HD_01_(\d{6})(\d{4})_")


@dataclass(frozen=True)
class HyperDeck:
    name: str
    ip: str
    volumes: tuple[str, ...]


@dataclass(frozen=True)
class RemoteFile:
    slot: str
    name: str
    size: int | None
    modified_at: dt.datetime | None


class SyncError(Exception):
    """Raised when a sync operation fails in a non-recoverable way."""


@dataclass(frozen=True)
class PredictedRename:
    raw_name: str
    final_name: str
    final_path: Path


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


def parse_args() -> argparse.Namespace:
    defaults = load_config()
    parser = argparse.ArgumentParser(
        description="Sync HyperDeck files via ftplib.",
    )
    parser.add_argument("hyperdeck", help="HyperDeck name (e.g. HD1) or IP address")
    parser.add_argument(
        "destination",
        nargs="?",
        default=str(defaults.downloads_dir),
        help="Destination root for downloaded files",
    )
    parser.add_argument(
        "--sync-while-recording",
        action="store_true",
        help="Allow file sync while the HyperDeck is actively recording",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without writing files",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Path to the HyperDeck YAML config",
    )
    parser.add_argument(
        "--log-file",
        default=str(defaults.log_file),
        help="Path to the shared log file",
    )
    return parser.parse_args()


def resolve_hyperdeck(hyperdeck_input: str, hyperdecks: Iterable[HyperDeckConfig]) -> HyperDeck:
    for deck in hyperdecks:
        if deck.name == hyperdeck_input:
            return HyperDeck(name=deck.name, ip=deck.ip, volumes=deck.volumes)
    return HyperDeck(name=hyperdeck_input, ip=hyperdeck_input, volumes=tuple(sorted(VALID_SLOTS)))


def preflight_network_check(deck: HyperDeck, log_file: Path) -> bool:
    try:
        with socket.create_connection((deck.ip, FTP_PORT), timeout=SOCKET_TIMEOUT_SECONDS):
            return True
    except OSError:
        log(
            f"❌ Preflight network check failed for {deck.name} ({deck.ip}): FTP port 21 is unreachable.",
            log_file,
        )
        return False


def query_transport_info(deck: HyperDeck) -> str | None:
    try:
        with socket.create_connection((deck.ip, TRANSPORT_PORT), timeout=3) as sock:
            sock.sendall(b"transport info\rquit\r")
            sock.shutdown(socket.SHUT_WR)
            return sock.recv(4096).decode("utf-8", errors="replace").replace("\r", "")
    except OSError:
        return None


def check_recording_status(deck: HyperDeck, allow_sync_when_recording: bool, dry_run: bool, log_file: Path) -> bool:
    if dry_run:
        log("🧪 Dry run: skipping recording-status check.", log_file)
        return True

    response = query_transport_info(deck)
    if response is None:
        log(f"⚠️ Could not query recording status on {deck.name} ({deck.ip}); proceeding with sync.", log_file)
        return True

    if "status: record" not in response.lower():
        return True

    if allow_sync_when_recording:
        log(
            f"⚠️ Warning: Recording detected on {deck.name} ({deck.ip}), but proceeding due to override flag.",
            log_file,
        )
        return True

    log(f"🎬 Recording detected on {deck.name} ({deck.ip}). Skipping file transfers.", log_file)
    return False


def ftp_connect(deck: HyperDeck) -> ftplib.FTP:
    ftp = ftplib.FTP(timeout=SOCKET_TIMEOUT_SECONDS)
    ftp.connect(deck.ip, FTP_PORT)
    ftp.login()
    return ftp


def discover_slots(deck: HyperDeck, log_file: Path) -> list[str]:
    failure_reason = "unknown FTP error"
    for attempt in range(1, SLOT_DISCOVERY_ATTEMPTS + 1):
        try:
            with ftp_connect(deck) as ftp:
                slots = []
                for entry in ftp.nlst():
                    cleaned = entry.rstrip("/").split("/")[-1]
                    if cleaned in VALID_SLOTS:
                        slots.append(cleaned)
                return sorted(set(slots))
        except Exception as exc:  # noqa: BLE001
            failure_reason = str(exc) or failure_reason
            if attempt < SLOT_DISCOVERY_ATTEMPTS:
                log(
                    f"⚠️ Slot discovery attempt {attempt}/{SLOT_DISCOVERY_ATTEMPTS} failed for "
                    f"{deck.name} ({deck.ip}): {failure_reason} Retrying in {SLOT_DISCOVERY_SLEEP_SECONDS}s...",
                    log_file,
                )
                time.sleep(SLOT_DISCOVERY_SLEEP_SECONDS)

    raise SyncError(
        f"Failed to query media slots on {deck.name} ({deck.ip}) after "
        f"{SLOT_DISCOVERY_ATTEMPTS} attempt(s): {failure_reason}"
    )


def parse_mdtm_response(response: str) -> dt.datetime | None:
    parts = response.strip().split()
    if len(parts) != 2:
        return None
    try:
        return dt.datetime.strptime(parts[1], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def parse_list_timestamp(month: str, day: str, time_or_year: str) -> dt.datetime | None:
    now_utc = dt.datetime.now(dt.timezone.utc)
    if ":" in time_or_year:
        year = now_utc.year
        raw_value = f"{year} {month} {day} {time_or_year}"
        try:
            parsed = dt.datetime.strptime(raw_value, "%Y %b %d %H:%M")
        except ValueError:
            return None
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
        if parsed > now_utc + dt.timedelta(days=1):
            parsed = parsed.replace(year=parsed.year - 1)
        return parsed

    raw_value = f"{month} {day} {time_or_year}"
    try:
        return dt.datetime.strptime(raw_value, "%b %d %Y").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def hhmm_to_minutes(value: str) -> int:
    hours, minutes = value.split(":", 1)
    return int(hours) * 60 + int(minutes)


def within_tolerance(value: int, target: int, tolerance: int) -> bool:
    return (target - tolerance) <= value <= (target + tolerance)


def label_for_time(minutes: int, tolerance: int, service_windows: tuple[ServiceWindow, ...]) -> str:
    for window in service_windows:
        if within_tolerance(minutes, window.minutes, tolerance):
            return window.label
    return ""


def most_recent_sunday(now: dt.datetime | None = None) -> dt.date:
    current = now or dt.datetime.now()
    days_since_sunday = (current.weekday() + 1) % 7
    return (current - dt.timedelta(days=days_since_sunday)).date()


def predict_final_name(
    deck: HyperDeck,
    remote_file: RemoteFile,
    local_dir: Path,
    tolerance: int,
    hd1_services: tuple[ServiceWindow, ...],
    hd2_services: tuple[ServiceWindow, ...],
) -> PredictedRename | None:
    if deck.name == "HD1":
        match = HD1_FILENAME_RE.search(remote_file.name)
        if not match:
            return None
        date_part, time_part = match.groups()
        utc_value = (
            f"20{date_part[0:2]}-{date_part[2:4]}-{date_part[4:6]} "
            f"{time_part[0:2]}:{time_part[2:4]}:00"
        )
        try:
            local_recording_time = (
                dt.datetime.strptime(utc_value, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=dt.timezone.utc)
                .astimezone()
            )
        except ValueError:
            return None

        service_date = local_recording_time.strftime("%Y-%m-%d")
        local_hhmm = local_recording_time.strftime("%H:%M")
        label = label_for_time(hhmm_to_minutes(local_hhmm), tolerance, hd1_services)
        if not label:
            return None

        final_name = f"HD1_ROC_{service_date}_{label}.mp4"
        return PredictedRename(remote_file.name, final_name, local_dir / final_name)

    if deck.name == "HD2" and remote_file.modified_at is not None:
        local_recording_time = remote_file.modified_at.astimezone()
        service_date = local_recording_time.strftime("%Y-%m-%d")
        local_hhmm = local_recording_time.strftime("%H:%M")
        label = label_for_time(hhmm_to_minutes(local_hhmm), tolerance, hd2_services)
        if not label:
            return None

        final_name = f"HD2_ONL_{service_date}_{label}.mp4"
        return PredictedRename(remote_file.name, final_name, local_dir / final_name)

    return None


def list_remote_files_via_list(ftp: ftplib.FTP, slot: str) -> list[RemoteFile]:
    lines: list[str] = []
    ftp.retrlines(f"LIST {slot}", lines.append)

    remote_files: list[RemoteFile] = []
    for line in lines:
        parts = line.split(maxsplit=8)
        if len(parts) < 9:
            continue
        file_type = parts[0][0]
        if file_type != "-":
            continue

        name = parts[8]
        if not name.lower().endswith(".mp4"):
            continue

        try:
            size = int(parts[4])
        except ValueError:
            size = None

        modified_at = parse_list_timestamp(parts[5], parts[6], parts[7])
        remote_files.append(RemoteFile(slot=slot, name=name, size=size, modified_at=modified_at))

    return sorted(remote_files, key=lambda item: item.name)


def stat_remote_file(ftp: ftplib.FTP, slot: str, name: str) -> RemoteFile:
    size: int | None = None
    modified_at: dt.datetime | None = None
    original_dir = ftp.pwd()

    try:
        ftp.cwd(slot)

        try:
            size = ftp.size(name)
        except Exception:  # noqa: BLE001
            size = None

        try:
            modified_at = parse_mdtm_response(ftp.sendcmd(f"MDTM {name}"))
        except Exception:  # noqa: BLE001
            modified_at = None
    finally:
        ftp.cwd(original_dir)

    return RemoteFile(slot=slot, name=name, size=size, modified_at=modified_at)


def list_remote_files(ftp: ftplib.FTP, slot: str) -> list[RemoteFile]:
    try:
        remote_files = list_remote_files_via_list(ftp, slot)
        if remote_files:
            return remote_files
    except Exception:  # noqa: BLE001
        pass

    names = []
    for entry in ftp.nlst(slot):
        cleaned = entry.rstrip("/").split("/")[-1]
        if not cleaned or cleaned.startswith("."):
            continue
        names.append(cleaned)

    files = [stat_remote_file(ftp, slot, name) for name in sorted(set(names))]
    return [item for item in files if item.name.lower().endswith(".mp4")]


def local_file_is_current(local_path: Path, remote_file: RemoteFile) -> bool:
    if not local_path.exists():
        return False

    local_size = local_path.stat().st_size
    if remote_file.size is not None and local_size != remote_file.size:
        return False

    if remote_file.modified_at is None:
        return True

    local_mtime = dt.datetime.fromtimestamp(local_path.stat().st_mtime, tz=dt.timezone.utc)
    return local_mtime >= remote_file.modified_at


def set_local_mtime(local_path: Path, modified_at: dt.datetime | None) -> None:
    if modified_at is None:
        return
    epoch = modified_at.timestamp()
    os.utime(local_path, (epoch, epoch))


def download_file(ftp: ftplib.FTP, remote_file: RemoteFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False, prefix=destination.name + ".", suffix=".part") as handle:
        temp_path = Path(handle.name)
        try:
            ftp.retrbinary(f"RETR {remote_file.slot}/{remote_file.name}", handle.write)
            handle.flush()
            os.fsync(handle.fileno())
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    temp_path.replace(destination)
    os.chmod(destination, DOWNLOADED_FILE_MODE)
    set_local_mtime(destination, remote_file.modified_at)


def sync_slot(
    deck: HyperDeck,
    slot: str,
    local_dir: Path,
    dry_run: bool,
    log_file: Path,
    tolerance: int,
    hd1_services: tuple[ServiceWindow, ...],
    hd2_services: tuple[ServiceWindow, ...],
) -> int:
    local_dir.mkdir(parents=True, exist_ok=True)
    transferred = 0

    with ftp_connect(deck) as ftp:
        remote_files = list_remote_files(ftp, slot)
        for remote_file in remote_files:
            local_path = local_dir / remote_file.name
            predicted = predict_final_name(deck, remote_file, local_dir, tolerance, hd1_services, hd2_services)
            if predicted is not None and local_file_is_current(predicted.final_path, remote_file):
                log(f"⏭️ Already processed: {predicted.raw_name} -> {predicted.final_name}", log_file)
                continue
            if local_file_is_current(local_path, remote_file):
                continue

            if dry_run:
                log(f"🧪 (Dry Run) Would transfer: {slot}/{remote_file.name}", log_file)
                transferred += 1
                continue

            download_file(ftp, remote_file, local_path)
            log(f"📁 Transferred: {remote_file.name}", log_file)
            transferred += 1

    return transferred


def main() -> int:
    args = parse_args()
    log_file = Path(args.log_file).expanduser()
    destination_root = Path(args.destination).expanduser()
    destination_root.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        log("🧪 Dry run mode active — no files will be copied.", log_file)

    config = load_config(Path(args.config).expanduser())
    deck = resolve_hyperdeck(args.hyperdeck, config.hyperdecks)

    log(
        f"Using argument: '{args.hyperdeck}'. Resolved HyperDeck: {deck.name} ({deck.ip}). "
        f"Sync while recording: {str(args.sync_while_recording).lower()}",
        log_file,
    )
    log(f"🔁 Starting HyperDeck sync for {deck.name} ({deck.ip})...", log_file)

    if not check_recording_status(deck, args.sync_while_recording, args.dry_run, log_file):
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write("\n")
        return 0

    if not preflight_network_check(deck, log_file):
        return 1

    log(f"📡 Discovering available media slots on {deck.name} ({deck.ip})...", log_file)
    try:
        slots = discover_slots(deck, log_file)
    except SyncError as exc:
        log(f"❌ {exc}", log_file)
        return 1

    configured_slots = {slot for slot in deck.volumes if slot in VALID_SLOTS}
    if configured_slots:
        slots = [slot for slot in slots if slot in configured_slots]

    if not slots:
        log(f"⚠️ No valid media slots found on {deck.name} ({deck.ip}). Exiting.", log_file)
        return 1

    total_transferred = 0
    failed_slots: list[str] = []
    for slot in slots:
        local_dir = destination_root / slot / slot
        log(f"🔄 Syncing {slot} from {deck.name} ({deck.ip}) to {local_dir}...", log_file)
        try:
            slot_transferred = sync_slot(
                deck,
                slot,
                local_dir,
                args.dry_run,
                log_file,
                config.time_tolerance_min,
                config.hd1_services,
                config.hd2_services,
            )
        except Exception as exc:  # noqa: BLE001
            log(f"❌ Sync failed for slot {slot} on {deck.name} ({deck.ip}): {exc}", log_file)
            failed_slots.append(slot)
            continue

        log(f"✅ {slot} sync complete. Transferred {slot_transferred} file(s).", log_file)
        total_transferred += slot_transferred

    log(
        f"✅ All syncs complete for {deck.name} ({deck.ip}). Total files transferred: {total_transferred}.",
        log_file,
    )
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    if failed_slots:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
