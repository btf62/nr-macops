#!/usr/bin/env python3
import os, sys, time, json, socket, subprocess, smtplib
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable
from email.message import EmailMessage

from spotipy import Spotify
from spotipy.exceptions import SpotifyOauthError
from spotipy.oauth2 import SpotifyOAuth

# Defaults (can be overridden via env)
LOG_FILE = os.environ.get("SPOTIFY_LOG_FILE", "/usr/local/var/log/spotify/spotify.log")
EMAIL_TO = os.environ.get("SPOTIFY_EMAIL_TO", "bfiles@northridgerochester.com")
EMAIL_BACKEND = os.environ.get("SPOTIFY_EMAIL_BACKEND", "mail").lower()  # "mail" or "smtp"

def spotify_cache_path() -> Optional[str]:
    cache_path = os.environ.get("SPOTIPY_CACHE_PATH")
    if not cache_path:
        return None
    return os.path.expanduser(cache_path)

def spotify_client(script_name: str, scopes: str) -> Spotify:
    cache_path = spotify_cache_path()
    if cache_path:
        log_and_stdout(script_name, f"[i] Using Spotify token cache: {cache_path}")
    else:
        log_and_stdout(script_name, "⚠️ SPOTIPY_CACHE_PATH is not set; Spotipy will use its default cache path.")

    return Spotify(
        auth_manager=SpotifyOAuth(
            scope=scopes,
            cache_path=cache_path,
        )
    )

def is_spotify_authorization_error(exc: Exception) -> bool:
    text = " ".join(
        str(part)
        for part in [
            getattr(exc, "msg", ""),
            getattr(exc, "reason", ""),
            getattr(exc, "error", ""),
            getattr(exc, "error_description", ""),
            str(exc),
        ]
        if part
    ).lower()

    return isinstance(exc, SpotifyOauthError) or "invalid_grant" in text

def handle_spotify_authorization_error(script_name: str, exc: Exception) -> bool:
    if not is_spotify_authorization_error(exc):
        return False

    log_and_stdout(script_name, "❌ Spotify authorization expired or invalid; interactive reauthorization is required.")
    log_and_stdout(script_name, f"    Error type: {type(exc).__name__}")

    cache_path = spotify_cache_path()
    if cache_path:
        path = Path(cache_path)
        if path.exists():
            try:
                path.unlink()
                log_and_stdout(script_name, f"Removed expired Spotify token cache: {path}")
            except OSError as remove_error:
                log_and_stdout(script_name, f"⚠️ Could not remove Spotify token cache {path}: {remove_error}")
        else:
            log_and_stdout(script_name, f"[i] Configured Spotify token cache was already absent: {path}")
    else:
        log_and_stdout(script_name, "⚠️ No SPOTIPY_CACHE_PATH configured; leaving Spotipy default cache files untouched.")

    return True

def spotify_reauthorization_instructions() -> str:
    cache_path = spotify_cache_path() or "(SPOTIPY_CACHE_PATH is not set)"
    return f"""
Spotify authorization expired or was revoked. ONL Audio needs interactive Spotify reauthorization.

Run this from an interactive ONL Audio shell:

cd ~/scripts
. "$HOME/scripts/spotify_env.sh"
rm -f "{cache_path}"
python3 spotify_auth_smoke_test.py
""".strip()

def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_and_stdout(script_name: str, msg: str):
    """Append a timestamped line to console + log file."""
    line = f"[{timestamp()}] [{script_name}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def tail_lines(path: str, n: int = 20) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-n:])
    except FileNotFoundError:
        return "(log file not found)\n"

def _hostname_alias() -> str:
    return os.environ.get("SPOTIFY_HOST_ALIAS") or socket.gethostname()

def _echo_pipe(body: str):
    """Utility to pipe a string into a subprocess."""
    return subprocess.Popen(["/bin/echo", body], stdout=subprocess.PIPE)

def send_mail(script_name: str, subject: str, body: str, to_addrs: str):
    """Try /usr/bin/mail; if that fails (or backend=smtp), try SMTP env."""
    backend = os.environ.get("SPOTIFY_EMAIL_BACKEND", "mail").lower()
    recipients = to_addrs.split()
    subject = f"[{_hostname_alias()}] {subject}"

    # use the shared logger; no callable argument needed from callers
    def _log(msg: str):
        from spotify_utils import log_and_stdout  # safe local import to avoid cycles
        log_and_stdout(script_name, msg)

    _log(f"ℹ️ Email config: backend={backend}, to={recipients}")

    if backend == "mail":
        try:
            p1 = subprocess.Popen(["/bin/echo", body], stdout=subprocess.PIPE)
            subprocess.check_call(["/usr/bin/mail", "-s", subject, *recipients], stdin=p1.stdout)
            _log(f"✅ Email sent via /usr/bin/mail to {recipients}")
            return
        except Exception as e:
            _log(f"⚠️ /usr/bin/mail failed: {e}. Will try SMTP if configured…")

    # SMTP fallback
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_tls  = os.environ.get("SMTP_TLS", "1") not in ("0","false","False","no","NO")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user or "")

    if not (smtp_host and smtp_user and smtp_pass):
        _log("❌ SMTP not configured (set SMTP_HOST/SMTP_USER/SMTP_PASS). Email not sent.")
        return

    try:
        msg = EmailMessage()
        msg["From"] = smtp_from or smtp_user
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as s:
            if smtp_tls:
                s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        _log(f"✅ Email sent via SMTP to {recipients}")
    except Exception as e:
        _log(f"❌ SMTP send failed: {e}")

def need_env(script_name: str, key: str) -> str:
    v = os.environ.get(key)
    if not v:
        log_and_stdout(script_name, f"❌ Missing required env var: {key}")
        sys.exit(2)
    return v

def ensure_spotify_running(script_name: str):
    try:
        subprocess.run(["/usr/bin/open", "-ga", "Spotify"], check=True)
        log_and_stdout(script_name, "Launched/activated Spotify.app.")
    except subprocess.CalledProcessError:
        log_and_stdout(script_name, "⚠️ Could not launch Spotify.app")

def find_device(sp, name: str, retries: int = 10, delay: float = 1.0) -> Optional[dict]:
    """Canonical device lookup: 10 retries, 1.0s delay."""
    for _ in range(retries):
        devs = sp.devices().get("devices", [])
        for d in devs:
            if d.get("name") == name:
                return d
        time.sleep(delay)
    return None

def set_volume_and_verify(sp, device_id: str, target: int, script_name: str, device_name: str,
                          retries: int = 3, delay: float = 0.8):
    """
    Set Spotify Connect device volume to `target` (0–100), with retries and verification.
    Logs with log_and_stdout(script_name, ...).

    Uses current_playback() first to verify; falls back to devices() listing if needed.
    Skips setting if the device reports is_restricted=True.
    """
    # Sanitize target
    try:
        target = int(target)
    except Exception:
        target = 100
    target = max(0, min(100, target))

    # Check restriction flag (best-effort)
    try:
        devs = sp.devices().get("devices", [])
        me = next((d for d in devs if d.get("id") == device_id), None)
        if me and me.get("is_restricted"):
            log_and_stdout(script_name, f"ℹ️ Device '{device_name}' is restricted; skipping volume set.")
            return
    except Exception as e:
        log_and_stdout(script_name, f"⚠️ Could not inspect device restrictions: {e}")

    # Try to set volume
    for attempt in range(1, retries + 1):
        try:
            sp.volume(target, device_id=device_id)
            log_and_stdout(script_name, f"✅ Set volume to {target}% on '{device_name}'.")
            break
        except Exception as e:
            log_and_stdout(script_name, f"⚠️ Volume set attempt {attempt} failed: {e}. Retrying…")
            time.sleep(delay)
    else:
        log_and_stdout(script_name, f"⚠️ Could not set volume to {target}% after {retries} attempts.")
        return

    # Verify via current_playback (preferred), else via devices()
    try:
        time.sleep(0.5)
        pb = sp.current_playback()
        if pb and pb.get("device") and pb["device"].get("id") == device_id:
            vp = pb["device"].get("volume_percent")
            if vp is not None:
                log_and_stdout(script_name, f"ℹ️ Reported device volume: {vp}%")
                return
    except Exception as e:
        log_and_stdout(script_name, f"⚠️ Could not verify via current_playback: {e}")

    # Fallback verification
    try:
        devs = sp.devices().get("devices", [])
        me = next((d for d in devs if d.get("id") == device_id), None)
        if me and me.get("volume_percent") is not None:
            log_and_stdout(script_name, f"ℹ️ Reported device volume (fallback): {me['volume_percent']}%")
    except Exception as e:
        log_and_stdout(script_name, f"⚠️ Could not verify via devices(): {e}")

def print_devices(script_name: str, sp):
    devs = sp.devices().get("devices", [])
    if not devs:
        log_and_stdout(script_name, "ℹ️ No devices visible.")
        return
    log_and_stdout(script_name, "ℹ️ Available devices:")
    for d in devs:
        log_and_stdout(script_name, f"    - name={d.get('name')!r}, type={d.get('type')}, id={d.get('id')}, "
                                    f"active={d.get('is_active')}, restricted={d.get('is_restricted')}")
