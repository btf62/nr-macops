#!/usr/bin/env python3
import os, sys, time, subprocess

from spotify_utils import (
    LOG_FILE, EMAIL_TO,
    log_and_stdout, tail_lines, send_mail, need_env,
    ensure_spotify_running, find_device, print_devices,
    spotify_client, handle_spotify_authorization_error,
    spotify_reauthorization_instructions,
)

SCRIPT_NAME = "stop_outside_spotify.py"
SCOPES = "user-read-playback-state user-modify-playback-state"

def main():
    log_and_stdout(SCRIPT_NAME, "⏹️  Begin stop flow.")
    log_and_stdout(SCRIPT_NAME, f"[i] Using log file: {LOG_FILE}")
    log_and_stdout(SCRIPT_NAME, f"[i] Will email: {EMAIL_TO}")

    subject = "⏹️ Spotify Stop - Done"
    email_body_prefix = ""
    auth_failed = False
    target_name = need_env(SCRIPT_NAME, "SPOTIPY_DEVICE_NAME")
    fallback_name = os.environ.get("SPOTIPY_FALLBACK_DEVICE_NAME", "This computer")

    try:
        sp = spotify_client(SCRIPT_NAME, SCOPES)

        target = find_device(sp, target_name)
        if target:
            try:
                sp.pause_playback(device_id=target["id"])
                log_and_stdout(SCRIPT_NAME, f"✅ Paused device '{target_name}'.")
            except Exception as e:
                log_and_stdout(SCRIPT_NAME, f"⚠️ Pause on '{target_name}' failed/not allowed: {e}")
        else:
            log_and_stdout(SCRIPT_NAME, f"[i] Device '{target_name}' not found. Attempting to pause active player.")
            try:
                sp.pause_playback()
                log_and_stdout(SCRIPT_NAME, "Issued pause to the active device.")
            except Exception as e:
                log_and_stdout(SCRIPT_NAME, f"⚠️ Active-device pause failed: {e}")

        fb = find_device(sp, fallback_name)
        if fb:
            try:
                sp.transfer_playback(device_id=fb["id"], force_play=False)
                log_and_stdout(SCRIPT_NAME, f"✅ Transferred active device to '{fallback_name}' (no autoplay).")
            except Exception as e:
                log_and_stdout(SCRIPT_NAME, f"⚠️ Transfer to '{fallback_name}' failed: {e}")
        else:
            log_and_stdout(SCRIPT_NAME, f"[i] Fallback '{fallback_name}' not visible. Open Spotify on this Mac if you want it available.")
            print_devices(SCRIPT_NAME, sp)

        # Quit Spotify app on this Mac
        try:
            subprocess.run(["osascript", "-e", 'tell application "Spotify" to quit'])
            log_and_stdout(SCRIPT_NAME, "Quit Spotify.app on this Mac.")
        except Exception as e:
            log_and_stdout(SCRIPT_NAME, f"⚠️ Could not quit Spotify.app: {e}")

    except Exception as e:
        if handle_spotify_authorization_error(SCRIPT_NAME, e):
            subject = "⏹️ Spotify Stop - REAUTH REQUIRED"
            email_body_prefix = spotify_reauthorization_instructions() + "\n\n"
            auth_failed = True
        else:
            raise
    finally:
        body = email_body_prefix + tail_lines(LOG_FILE, 20)
        send_mail(SCRIPT_NAME, f"{subject} (target='{target_name}', fallback='{fallback_name}')", body, EMAIL_TO)
        log_and_stdout(SCRIPT_NAME, "🏁 Stop flow complete.\n")

    if auth_failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
