#!/usr/bin/env python3
import argparse
from pathlib import Path

from spotify_utils import spotify_cache_path, spotify_client

SCOPES = "user-read-playback-state user-modify-playback-state"


def main():
    parser = argparse.ArgumentParser(
        description="Verify Spotify authorization without starting playback."
    )
    parser.add_argument(
        "--reset-cache",
        action="store_true",
        help="Delete the configured Spotify token cache before testing.",
    )
    args = parser.parse_args()

    cache_path = spotify_cache_path()
    if args.reset_cache and cache_path:
        path = Path(cache_path)
        if path.exists():
            path.unlink()
            print(f"Removed Spotify token cache: {path}")
        else:
            print(f"Spotify token cache was already absent: {path}")

    sp = spotify_client("spotify_auth_smoke_test.py", SCOPES)
    user = sp.current_user()
    devices = sp.devices().get("devices", [])

    print(f"Spotify user: {user.get('id')}")
    print("Devices visible:")
    for device in devices:
        print(f"- {device.get('name')} ({device.get('type')})")


if __name__ == "__main__":
    main()
