#!/usr/bin/env python3
"""
rename_files.py

Python implementation of HyperDeck file renaming based on service-day time
windows. It mirrors the current rename_files.sh behavior so it can be adopted
incrementally without changing the established filename rules.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

from pipeline_config import CONFIG_PATH, ServiceWindow, load_config


SCRIPT_NAME = "rename_files.py"
HD1_FILENAME_RE = re.compile(r"HD_01_(\d{6})(\d{4})_")


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
        description="Rename HyperDeck recordings based on service windows.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show rename actions without modifying files",
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
        "--time-tolerance-min",
        type=int,
        default=defaults.time_tolerance_min,
        help="Service-window matching tolerance in minutes",
    )
    parser.add_argument(
        "base_dir",
        nargs="?",
        default=str(defaults.downloads_dir),
        help="Base HyperDeck download directory",
    )
    return parser.parse_args()


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


def format_local_hhmm_from_timestamp(epoch_seconds: float) -> str:
    return dt.datetime.fromtimestamp(epoch_seconds).strftime("%H:%M")


def rename_file(source: Path, destination: Path, dry_run: bool, log_file: Path) -> None:
    if source == destination:
        log(f"↪️ Already named correctly: '{source.name}'", log_file)
        return

    if destination.exists():
        log(f"⚠️ Destination exists, skipping: '{destination.name}'", log_file)
        return

    if dry_run:
        log(f"🧪 (Dry Run) Would rename: '{source.name}' -> '{destination.name}'", log_file)
        return

    source.rename(destination)
    log(f"✏️ Renamed: '{source.name}' -> '{destination.name}'", log_file)


def iter_mp4_files(source_dir: Path) -> list[Path]:
    return sorted(path for path in source_dir.glob("*.mp4") if path.is_file())


def process_hd2(
    source_dir: Path,
    service_date: str,
    dry_run: bool,
    tolerance: int,
    service_windows: tuple[ServiceWindow, ...],
    log_file: Path,
) -> None:
    log(f"🔍 Processing HD2 files in {source_dir}", log_file)
    if not source_dir.is_dir():
        return

    for file_path in iter_mp4_files(source_dir):
        try:
            mod_hhmm = format_local_hhmm_from_timestamp(file_path.stat().st_mtime)
        except OSError:
            log(f"⚠️ Could not read mod time for '{file_path.name}'", log_file)
            continue

        label = label_for_time(hhmm_to_minutes(mod_hhmm), tolerance, service_windows)
        if not label:
            log(f"⚠️ No HD2 window match for '{file_path.name}' at local {mod_hhmm}", log_file)
            continue

        destination = source_dir / f"HD2_ONL_{service_date}_{label}.mp4"
        rename_file(file_path, destination, dry_run, log_file)


def parse_hd1_local_hhmm(filename: str) -> str | None:
    match = HD1_FILENAME_RE.search(filename)
    if not match:
        return None

    date_part, time_part = match.groups()
    utc_value = (
        f"20{date_part[0:2]}-{date_part[2:4]}-{date_part[4:6]} "
        f"{time_part[0:2]}:{time_part[2:4]}:00"
    )
    try:
        utc_dt = dt.datetime.strptime(utc_value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None

    return utc_dt.astimezone().strftime("%H:%M")


def process_hd1(
    source_dir: Path,
    service_date: str,
    dry_run: bool,
    tolerance: int,
    service_windows: tuple[ServiceWindow, ...],
    log_file: Path,
) -> None:
    log(f"🔍 Processing HD1 files in {source_dir}", log_file)
    if not source_dir.is_dir():
        return

    for file_path in iter_mp4_files(source_dir):
        local_hhmm = parse_hd1_local_hhmm(file_path.name)
        if local_hhmm is None:
            if HD1_FILENAME_RE.search(file_path.name):
                log(f"⚠️ Could not parse UTC timestamp for '{file_path.name}'", log_file)
            else:
                log(f"⚠️ Filename does not match expected HD1 source pattern: '{file_path.name}'", log_file)
            continue

        label = label_for_time(hhmm_to_minutes(local_hhmm), tolerance, service_windows)
        if not label:
            log(f"⚠️ No HD1 window match for '{file_path.name}' at local {local_hhmm}", log_file)
            continue

        destination = source_dir / f"HD1_ROC_{service_date}_{label}.mp4"
        rename_file(file_path, destination, dry_run, log_file)


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config).expanduser())
    base_dir = Path(args.base_dir).expanduser()
    log_file = Path(args.log_file).expanduser()

    hd2_sources = [base_dir / "1" / "1", base_dir / "2" / "2"]
    hd1_sources = [base_dir / "sd1" / "sd1", base_dir / "sd2" / "sd2"]

    ensure_log_parent(log_file)
    log_file.touch(exist_ok=True)

    log("🚀 Starting file rename process...", log_file)
    log(f"📁 Base directory: {base_dir}", log_file)
    log(f"🕒 Start-time tolerance: +/- {args.time_tolerance_min} minute(s)", log_file)

    for source_dir in hd1_sources:
        if not source_dir.is_dir():
            log(f"⚠️ HD1 source directory not found: {source_dir}", log_file)
    for source_dir in hd2_sources:
        if not source_dir.is_dir():
            log(f"⚠️ HD2 source directory not found: {source_dir}", log_file)

    service_date = most_recent_sunday().strftime("%Y-%m-%d")
    log(f"📅 Using service date: {service_date}", log_file)

    for source_dir in hd2_sources:
        process_hd2(
            source_dir,
            service_date,
            args.dry_run,
            args.time_tolerance_min,
            config.hd2_services,
            log_file,
        )
    log("✅ HD2 rename pass complete.", log_file)

    for source_dir in hd1_sources:
        process_hd1(
            source_dir,
            service_date,
            args.dry_run,
            args.time_tolerance_min,
            config.hd1_services,
            log_file,
        )
    log("✅ HD1 rename pass complete.", log_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
