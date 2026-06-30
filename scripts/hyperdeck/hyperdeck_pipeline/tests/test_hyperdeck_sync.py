#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path


BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from hyperdeck_sync import (  # noqa: E402
    HyperDeck,
    RemoteFile,
    local_file_is_current,
    predict_final_name,
)
from pipeline_config import load_config  # noqa: E402


class HyperDeckSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config()

    def test_hd1_predicted_rename_matches_existing_processed_file(self) -> None:
        deck = HyperDeck(name="HD1", ip="10.20.193.141", volumes=("sd1", "sd2"))
        remote_file = RemoteFile(
            slot="sd1",
            name="HD_01_2603291225_0010.mp4",
            size=1234,
            modified_at=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            local_dir = Path(tmpdir)
            predicted = predict_final_name(
                deck,
                remote_file,
                local_dir,
                self.config.time_tolerance_min,
                self.config.hd1_services,
                self.config.hd2_services,
            )

            self.assertIsNotNone(predicted)
            assert predicted is not None
            self.assertEqual(predicted.final_name, "HD1_ROC_2026-03-29_08-30am.mp4")

            predicted.final_path.write_bytes(b"x" * remote_file.size)
            self.assertTrue(local_file_is_current(predicted.final_path, remote_file))

    def test_hd2_predicted_rename_uses_remote_timestamp_window(self) -> None:
        deck = HyperDeck(name="HD2", ip="10.20.193.113", volumes=("1", "2"))
        remote_file = RemoteFile(
            slot="1",
            name="Blackmagic HyperDeck Studio Mini_0007.mp4",
            size=4321,
            modified_at=dt.datetime(2026, 3, 29, 12, 53, tzinfo=dt.timezone.utc),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            local_dir = Path(tmpdir)
            predicted = predict_final_name(
                deck,
                remote_file,
                local_dir,
                self.config.time_tolerance_min,
                self.config.hd1_services,
                self.config.hd2_services,
            )

            self.assertIsNotNone(predicted)
            assert predicted is not None
            self.assertEqual(predicted.final_name, "HD2_ONL_2026-03-29_09-00am.mp4")


if __name__ == "__main__":
    unittest.main()
