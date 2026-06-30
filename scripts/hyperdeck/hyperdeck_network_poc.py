#!/usr/bin/env python3
"""
hyperdeck_network_poc.py

Diagnostic proof-of-concept: test network connectivity to HyperDeck devices
using only Python standard library (no lftp dependency).

Run this script from two contexts and compare the results:

  1. Directly from Terminal:
       python3 ~/scripts/hyperdeck_network_poc.py

  2. Via launchd (to simulate the background agent context):
       launchctl start com.northridge.hyperdeck.master-sync
       # then check: tail /usr/local/var/log/hyperdeck/network_poc.log

If TCP/FTP succeeds in Terminal but fails under launchd, the network
restriction is at the OS process-context level — not a shell/language issue.
This means a Python rewrite would still require the osascript Terminal wrapper.
"""

import datetime
import ftplib
import os
import socket
import sys

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HYPERDECKS = [
    {"name": "HD1", "ip": "10.20.193.141"},
    {"name": "HD2", "ip": "10.20.193.113"},
]

FTP_PORT = 21
TIMEOUT = 5
LOG_PATH = "/usr/local/var/log/hyperdeck/network_poc.log"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_tcp(name: str, ip: str) -> bool:
    """Test raw TCP connectivity to the FTP port."""
    try:
        with socket.create_connection((ip, FTP_PORT), timeout=TIMEOUT):
            log(f"  ✅ TCP  {name} ({ip}:{FTP_PORT}) — connected")
            return True
    except Exception as e:
        log(f"  ❌ TCP  {name} ({ip}:{FTP_PORT}) — {e}")
        return False


def test_ftp(name: str, ip: str) -> bool:
    """Test anonymous FTP login and root directory listing."""
    try:
        with ftplib.FTP(timeout=TIMEOUT) as ftp:
            ftp.connect(ip, FTP_PORT)
            ftp.login()  # HyperDecks accept anonymous FTP
            listing = ftp.nlst()
            log(f"  ✅ FTP  {name} ({ip}) — logged in, root: {listing}")
            return True
    except Exception as e:
        log(f"  ❌ FTP  {name} ({ip}) — {e}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    is_interactive = sys.stdout.isatty()
    context = "interactive terminal" if is_interactive else "non-interactive (launchd or redirected)"

    log("=" * 60)
    log(f"HyperDeck Network POC")
    log(f"  PID:     {os.getpid()}")
    log(f"  User:    {os.getenv('USER', 'unknown')}")
    log(f"  Context: {context}")
    log(f"  Python:  {sys.version.split()[0]}")
    log(f"  PATH:    {os.getenv('PATH', '(not set)')}")
    log("=" * 60)

    results = {}
    for hd in HYPERDECKS:
        name, ip = hd["name"], hd["ip"]
        log(f"{name} ({ip}):")
        tcp_ok = test_tcp(name, ip)
        ftp_ok = test_ftp(name, ip) if tcp_ok else False
        results[name] = {"tcp": tcp_ok, "ftp": ftp_ok}

    log("-" * 60)
    log("Summary:")
    all_ok = True
    for name, r in results.items():
        status = "✅ OK" if r["tcp"] and r["ftp"] else "❌ FAILED"
        log(f"  {name}: TCP={'OK' if r['tcp'] else 'FAIL'}, FTP={'OK' if r['ftp'] else 'FAIL'}  {status}")
        if not (r["tcp"] and r["ftp"]):
            all_ok = False

    log("=" * 60)
    log("POC complete.\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
