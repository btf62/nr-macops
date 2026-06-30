#!/usr/bin/env python3
"""
copy_to_gdrive.py

Python implementation of the HyperDeck Google Drive upload step. It keeps
`rclone` as the actual transport while porting the scan/date-selection logic
out of bash.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pipeline_config import CONFIG_PATH, load_config


SCRIPT_NAME = "copy_to_gdrive.py"
DATE_YYYY_MM_DD_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
DATE_YYMMDD_RE = re.compile(r"(\d{6})")


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
        description="Upload HyperDeck recordings to Google Drive via rclone.",
    )
    parser.add_argument(
        "scan_dir",
        nargs="?",
        default=str(defaults.downloads_dir),
        help="Directory tree to scan for MP4 files",
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
        "--gdrive-remote",
        default=defaults.upload_remote,
        help="Configured rclone remote name",
    )
    parser.add_argument(
        "--dest-base",
        default=defaults.upload_dest_base,
        help="Base folder inside the rclone remote",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show upload actions without executing rclone",
    )
    return parser.parse_args()


def find_media_files(scan_dir: Path, extension: str) -> list[Path]:
    return sorted(path for path in scan_dir.rglob(f"*{extension}") if path.is_file())


def date_from_filename(filename: str) -> dt.date | None:
    match = DATE_YYMMDD_RE.search(filename)
    if match:
        raw = match.group(1)
        try:
            return dt.datetime.strptime(f"20{raw}", "%Y%m%d").date()
        except ValueError:
            return None

    match = DATE_YYYY_MM_DD_RE.search(filename)
    if match:
        try:
            return dt.datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None

    return None


def latest_recording_date(paths: list[Path]) -> dt.date | None:
    dates = []
    for path in paths:
        found = date_from_filename(path.name)
        if found is not None:
            dates.append(found)
    if not dates:
        return None
    return max(dates)


def rclone_binary() -> str:
    binary = shutil.which("rclone")
    if not binary:
        raise RuntimeError("rclone command not found in PATH")
    return binary


def run_rclone_copy(source: Path, destination: str, dry_run: bool, log_file: Path) -> int:
    command = [rclone_binary(), "copy", str(source), destination, "--update", "--progress"]
    quoted = " ".join(subprocess.list2cmdline([part]) if " " in part else part for part in command)
    log(f"Executing: {quoted}", log_file)

    if dry_run:
        log(f"🧪 (Dry Run) Would upload: {source.name}", log_file)
        return 0

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
    print("", flush=True)
    return process.wait()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config).expanduser())
    scan_dir = Path(args.scan_dir).expanduser()
    log_file = Path(args.log_file).expanduser()

    ensure_log_parent(log_file)
    log_file.touch(exist_ok=True)

    log(f"📁 Scanning: {scan_dir}", log_file)
    files = find_media_files(scan_dir, config.upload_extension)
    latest_date = latest_recording_date(files)
    if latest_date is None:
        log("❌ No valid date patterns found in filenames.", log_file)
        return 1

    mmddyy = latest_date.strftime("%m.%d.%y")
    dest_path = f"{args.gdrive_remote}:{args.dest_base}/{mmddyy}"
    log(f"📆 Using latest recording date from filenames: {latest_date.isoformat()}", log_file)
    log(f"☁️ Remote destination folder: {dest_path}", log_file)

    for file_path in files:
        exit_code = run_rclone_copy(file_path, dest_path, args.dry_run, log_file)
        if exit_code != 0:
            log(f"❌ Upload failed for '{file_path.name}'", log_file)
            return exit_code

    log("✅ Upload complete.", log_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
