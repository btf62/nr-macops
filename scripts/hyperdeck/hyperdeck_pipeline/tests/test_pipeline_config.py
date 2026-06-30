#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import sys


BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from pipeline_config import default_config, load_config  # noqa: E402


class PipelineConfigTests(unittest.TestCase):
    def test_load_config_returns_defaults_when_file_is_missing(self) -> None:
        config = load_config(Path("/tmp/definitely_missing_hyperdeck_config.yaml"))
        defaults = default_config()

        self.assertEqual(config.downloads_dir, defaults.downloads_dir)
        self.assertEqual(config.log_file, defaults.log_file)
        self.assertEqual(config.hyperdecks, defaults.hyperdecks)

    def test_load_config_reads_shared_values_from_yaml(self) -> None:
        raw_config = textwrap.dedent(
            """
            hyperdecks:
              - name: HDX
                ip: 192.0.2.10
                volumes: ["alpha", "beta"]
            paths:
              downloads_dir: /tmp/custom_downloads
              log_file: /tmp/custom.log
            rename:
              time_tolerance_min: 5
              hd1_services:
                - time: "08:25"
                  label: "08-30am"
              hd2_services:
                - time: "08:54"
                  label: "09-00am"
            upload:
              remote: demo
              dest_base: Archive
              extension: ".mov"
            email:
              recipients:
                - one@example.com
                - two@example.com
              tail_lines: 25
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(raw_config, encoding="utf-8")
            config = load_config(config_path)

            self.assertEqual(config.hyperdecks[0].name, "HDX")
            self.assertEqual(config.hyperdecks[0].volumes, ("alpha", "beta"))
            self.assertEqual(config.downloads_dir, Path("/tmp/custom_downloads"))
            self.assertEqual(config.log_file, Path("/tmp/custom.log"))
            self.assertEqual(config.time_tolerance_min, 5)
            self.assertEqual(config.upload_remote, "demo")
            self.assertEqual(config.upload_dest_base, "Archive")
            self.assertEqual(config.upload_extension, ".mov")
            self.assertEqual(config.email_recipients, ("one@example.com", "two@example.com"))
            self.assertEqual(config.mail_tail_lines, 25)


if __name__ == "__main__":
    unittest.main()
