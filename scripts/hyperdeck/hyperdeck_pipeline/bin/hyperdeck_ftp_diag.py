#!/usr/bin/env python3
"""
hyperdeck_ftp_diag.py

Inspect raw FTP metadata for HyperDeck files so we can compare what the device
returns via ftplib with what the shell/lftp pipeline appears to preserve.
"""

from __future__ import annotations

import argparse
import ftplib
import sys


HYPERDECKS = {
    "HD1": "10.20.193.141",
    "HD2": "10.20.193.113",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print raw HyperDeck FTP metadata.")
    parser.add_argument("hyperdeck", help="HyperDeck name (HD1/HD2) or IP address")
    parser.add_argument("slot", help="FTP slot to inspect, e.g. 1 or sd1")
    return parser.parse_args()


def resolve_ip(raw_value: str) -> str:
    return HYPERDECKS.get(raw_value, raw_value)


def main() -> int:
    args = parse_args()
    ip = resolve_ip(args.hyperdeck)

    with ftplib.FTP(timeout=10) as ftp:
        ftp.connect(ip, 21)
        ftp.login()

        print(f"Connected to {args.hyperdeck} ({ip})")
        print(f"PWD: {ftp.pwd()}")
        print(f"NLST /: {ftp.nlst()}")
        print()

        print(f"NLST {args.slot}:")
        slot_entries = ftp.nlst(args.slot)
        for entry in slot_entries:
            print(f"  {entry}")
        print()

        print(f"LIST {args.slot}:")
        ftp.retrlines(f"LIST {args.slot}", lambda line: print(f"  {line}"))
        print()

        try:
            original_dir = ftp.pwd()
            ftp.cwd(args.slot)
            print(f"MLSD {args.slot}:")
            for name, facts in ftp.mlsd(facts=["modify", "size", "type"]):
                print(f"  {name!r} -> {facts}")
            ftp.cwd(original_dir)
            print()
        except Exception as exc:  # noqa: BLE001
            print(f"MLSD failed: {exc}")
            print()

        ftp.cwd(args.slot)
        names = sorted(
            entry.rstrip("/").split("/")[-1]
            for entry in slot_entries
            if entry.rstrip("/").split("/")[-1]
        )

        print("Per-file commands:")
        for name in names:
            print(f"  File: {name}")
            try:
                print(f"    SIZE (cwd): {ftp.size(name)}")
            except Exception as exc:  # noqa: BLE001
                print(f"    SIZE (cwd) failed: {exc}")

            try:
                print(f"    MDTM (cwd): {ftp.sendcmd(f'MDTM {name}')}")
            except Exception as exc:  # noqa: BLE001
                print(f"    MDTM (cwd) failed: {exc}")

            try:
                print(f"    SIZE (path): {ftp.size(f'{args.slot}/{name}')}")
            except Exception as exc:  # noqa: BLE001
                print(f"    SIZE (path) failed: {exc}")

            try:
                print(f"    MDTM (path): {ftp.sendcmd(f'MDTM {args.slot}/{name}')}")
            except Exception as exc:  # noqa: BLE001
                print(f"    MDTM (path) failed: {exc}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
