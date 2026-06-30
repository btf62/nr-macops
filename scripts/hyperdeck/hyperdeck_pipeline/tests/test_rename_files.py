#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from pipeline_config import load_config  # noqa: E402
from rename_files import (  # noqa: E402
    hhmm_to_minutes,
    label_for_time,
    parse_hd1_local_hhmm,
    process_hd2,
)


class RenameFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config()

    def test_parse_hd1_filename_maps_to_expected_local_time(self) -> None:
        self.assertEqual(parse_hd1_local_hhmm("HD_01_2603291225_0010.mp4"), "08:25")

    def test_hd2_service_window_honors_tolerance_boundaries(self) -> None:
        label_inside = label_for_time(
            hhmm_to_minutes("08:57"),
            self.config.time_tolerance_min,
            self.config.hd2_services,
        )
        label_outside = label_for_time(
            hhmm_to_minutes("08:58"),
            self.config.time_tolerance_min,
            self.config.hd2_services,
        )

        self.assertEqual(label_inside, "09-00am")
        self.assertEqual(label_outside, "")

    def test_process_hd2_dry_run_maps_mtime_to_expected_target_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            log_file = source_dir / "rename.log"
            file_path = source_dir / "Blackmagic HyperDeck Studio Mini_0007.mp4"
            file_path.write_bytes(b"demo")
            os.utime(file_path, (1774788780, 1774788780))  # 2026-03-29 12:53:00 UTC == 08:53 EDT

            process_hd2(
                source_dir=source_dir,
                service_date="2026-03-29",
                dry_run=True,
                tolerance=self.config.time_tolerance_min,
                service_windows=self.config.hd2_services,
                log_file=log_file,
            )

            log_text = log_file.read_text(encoding="utf-8")
            self.assertIn(
                "Would rename: 'Blackmagic HyperDeck Studio Mini_0007.mp4' -> 'HD2_ONL_2026-03-29_09-00am.mp4'",
                log_text,
            )


if __name__ == "__main__":
    unittest.main()
