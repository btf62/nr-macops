#!/usr/bin/env python3
import os, sys, time
from spotipy.exceptions import SpotifyException

from spotify_utils import (
    LOG_FILE, EMAIL_TO,
    log_and_stdout, tail_lines, send_mail, need_env,
    ensure_spotify_running, find_device, set_volume_and_verify,
    print_devices, spotify_client, handle_spotify_authorization_error,
    is_spotify_authorization_error, spotify_reauthorization_instructions,
)

SCRIPT_NAME = "connect_outside_spotify.py"
SCOPES = "user-read-playback-state user-modify-playback-state"

def main():
    log_and_stdout(SCRIPT_NAME, "▶️  Begin connect flow.")
    log_and_stdout(SCRIPT_NAME, f"[i] Using log file: {LOG_FILE}")
    log_and_stdout(SCRIPT_NAME, f"[i] Will email: {EMAIL_TO}")

    subject = "🎧 Spotify Connect - Unknown result"
    email_body_prefix = ""
    auth_failed = False
    try:
        playlist_id = need_env(SCRIPT_NAME, "SPOTIPY_PLAYLIST_ID")
        device_name = need_env(SCRIPT_NAME, "SPOTIPY_DEVICE_NAME")

        ensure_spotify_running(SCRIPT_NAME)

        sp = spotify_client(SCRIPT_NAME, SCOPES)

        dev = find_device(sp, device_name)
        if not dev:
            log_and_stdout(SCRIPT_NAME, f"Couldn't find device '{device_name}'.")
            print_devices(SCRIPT_NAME, sp)
            subject = f"🎧 Spotify Connect - FAILED ({device_name} not found)"
            return

        device_id = dev["id"]
        log_and_stdout(SCRIPT_NAME, f"Found device '{device_name}' (id={device_id}). Transferring playback (no autoplay).")
        sp.transfer_playback(device_id=device_id, force_play=False)

        # target volume: env override or default to 100
        target_volume = int(os.environ.get("SPOTIPY_TARGET_VOLUME", "100"))
        set_volume_and_verify(sp, device_id, target_volume, SCRIPT_NAME, device_name)

        # sequential loop
        sp.shuffle(state=False, device_id=device_id)
        sp.repeat(state="context", device_id=device_id)

        # sanity check
        try:
            pb = sp.current_playback()
            if pb:
                log_and_stdout(SCRIPT_NAME, f"[i] Verified playback mode: shuffle={pb.get('shuffle_state')}, repeat={pb.get('repeat_state')}")
            else:
                log_and_stdout(SCRIPT_NAME, "[i] Could not verify playback mode (no current_playback returned).")
        except Exception as e:
            log_and_stdout(SCRIPT_NAME, f"⚠️ Error verifying playback mode: {e}")

        time.sleep(0.8)
        context_uri = f"spotify:playlist:{playlist_id}"

        for attempt in range(1, 4):
            try:
                sp.start_playback(device_id=device_id, context_uri=context_uri, offset={"position": 0})
                log_and_stdout(SCRIPT_NAME, f"✅ Playing playlist {playlist_id} on '{device_name}' (shuffle=off, repeat=context).")
                subject = f"🎧 Spotify Connect - OK on '{device_name}'"
                return
            except SpotifyException as e:
                if is_spotify_authorization_error(e):
                    raise
                log_and_stdout(SCRIPT_NAME, f"Attempt {attempt} start failed: {e}. Retrying…")
                time.sleep(1.2)
                try:
                    sp.transfer_playback(device_id=device_id, force_play=False)
                except Exception:
                    pass

        log_and_stdout(SCRIPT_NAME, "❌ Could not start playback after retries.")
        subject = f"🎧 Spotify Connect - FAILED to start on '{device_name}'"

    except Exception as e:
        if handle_spotify_authorization_error(SCRIPT_NAME, e):
            subject = "🎧 Spotify Connect - REAUTH REQUIRED"
            email_body_prefix = spotify_reauthorization_instructions() + "\n\n"
            auth_failed = True
        else:
            raise
    finally:
        body = email_body_prefix + tail_lines(LOG_FILE, 20)
        send_mail(SCRIPT_NAME, subject, body, EMAIL_TO)
        log_and_stdout(SCRIPT_NAME, "🏁 Connect flow complete.\n")

    if auth_failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
