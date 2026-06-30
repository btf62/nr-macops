# Spotify Refresh Token Expiration Handoff

Date prepared: 2026-06-28

Use this handoff on ONL Audio, where the Spotify automation actually runs.

## Trigger

Brad received a Spotify for Developers email:

- Sender: Spotify no-reply@legal.spotify.com
- Subject: `Spotify for Developers - Action required: Spotify refresh tokens will expire starting July 20, 2026`
- Received: 2026-06-18 08:17 EDT

Spotify says refresh tokens issued by Spotify Developer apps will expire after
six months. Existing apps are affected starting 2026-07-20. When a refresh token
has expired, the token endpoint returns `invalid_grant`. Apps must discard the
stored token and send the user through authorization again.

Official references:

- https://developer.spotify.com/blog/2026-06-18-refresh-token-expiration
- https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens

## Why This Matters Here

The ONL Audio automation uses user-authenticated Spotify playback control, not
Client Credentials.

Relevant repo files:

- `spotify_env.sh`
- `connect_outside_spotify.py`
- `stop_outside_spotify.py`
- `spotify_utils.py`
- `cron.tab.onlaudio`

The start/stop scripts use Spotipy with:

```python
Spotify(auth_manager=SpotifyOAuth(scope=SCOPES))
```

Scopes:

```text
user-read-playback-state user-modify-playback-state
```

Those scopes require user authorization. The automation depends on a stored
Spotipy refresh token cache so cron can start and stop the Outside Spotify
playlist without someone signing in every Sunday.

## Likely Impact

Starting 2026-07-20, if the stored Spotify refresh token on ONL Audio is older
than six months, the next scheduled run may fail when Spotipy tries to refresh
the access token.

Operational symptom:

- Sunday playlist does not start at 7:59 AM, or stop script cannot authenticate.
- Logs may show `invalid_grant`, token refresh failure, or an auth prompt/link
  that cron cannot complete.

This is not fixed by repeatedly retrying the same cached token. Spotify's
direction is to discard the expired token and complete authorization again.

## ONL Audio Verification Steps

Run these on ONL Audio, not on another Mac:

```bash
cd ~/scripts
git status --short --branch
crontab -l | sed -n '1,90p'
python3 - <<'PY'
try:
    import spotipy
    print("spotipy import: OK")
    print("spotipy version:", getattr(spotipy, "__version__", "unknown"))
except Exception as exc:
    print("spotipy import: FAILED", exc)
PY
find "$HOME" -maxdepth 3 -type f \( -name '.cache' -o -name '.cache-*' -o -iname '*spotipy*' -o -iname '*spotify*cache*' \) -print 2>/dev/null
ls -la /usr/local/var/log/spotify 2>/dev/null || true
tail -n 120 /usr/local/var/log/spotify/spotify.log 2>/dev/null
tail -n 120 /usr/local/var/log/spotify/cron.log 2>/dev/null
```

Do not paste token values into chat. If inspecting a cache file, report only:

- path
- file modified time
- JSON keys present
- whether a `refresh_token` key exists
- `expires_at` / `expires_in` values if present
- whether logs show `invalid_grant`

Safe cache inspection helper:

```bash
python3 - <<'PY'
from pathlib import Path
import datetime
import json
import os

candidates = []
for root in [Path.home(), Path.cwd()]:
    for name in [".cache", ".cache-spotify", ".cache-spotipy"]:
        candidates.append(root / name)

seen = set()
for path in candidates:
    if path in seen:
        continue
    seen.add(path)
    if not path.exists() or not path.is_file():
        continue
    st = path.stat()
    print(f"{path}: present, mtime={datetime.datetime.fromtimestamp(st.st_mtime).isoformat()}")
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        print(f"  not JSON or unreadable: {exc}")
        continue
    safe = {k: data.get(k) for k in ["token_type", "scope", "expires_in", "expires_at"] if k in data}
    print(f"  keys={sorted(data.keys())}")
    print(f"  safe={safe}")
    print(f"  has_refresh_token={bool(data.get('refresh_token'))}")
PY
```

## Recommended Work

Target maintenance date: **Tuesday, 2026-07-07**.

Preferred implementation plan:

1. Add an explicit stable Spotipy cache path in `spotify_env.sh`, e.g.
   `SPOTIPY_CACHE_PATH="$HOME/.cache-northridge-outside-spotify-token.json"`.
   This removes ambiguity between Spotipy's default cache locations.
2. Add a shared Spotify auth helper in `spotify_utils.py` so both
   `connect_outside_spotify.py` and `stop_outside_spotify.py` construct
   `SpotifyOAuth` the same way and pass the configured cache path explicitly.
3. Add explicit expired/revoked-token handling around the first Spotify API
   calls:
   - detect `invalid_grant` / Spotipy OAuth failures
   - log a clear reauthorization-required message
   - remove only the configured cache file
   - send the existing failure email with reauthorization instructions
   - exit non-zero instead of retrying the same cached refresh token
4. Add a small manual reauthorization smoke test or runbook command that can be
   run interactively on ONL Audio and verifies `current_user()` / `devices()`
   without starting playback.
5. Reauthorize ONL Audio before Spotify's 2026-07-20 enforcement date, then
   add a recurring reminder to reauthorize at least every five months.

Credentials cleanup remains an important follow-up, but the July 2026
refresh-token change is the higher-priority operational risk.

## Suggested Code Direction

Keep the change small.

In `spotify_env.sh`, add a stable cache path, for example:

```bash
export SPOTIPY_CACHE_PATH="$HOME/.cache-northridge-outside-spotify-token.json"
```

On ONL Audio, Spotipy's legacy default cache is the file `$HOME/.cache`, so do
not use `$HOME/.cache/...` as a directory-style path unless the old file has
been deliberately migrated.

Then pass that to Spotipy explicitly in both Spotify scripts:

```python
auth_manager = SpotifyOAuth(
    scope=SCOPES,
    cache_path=os.environ.get("SPOTIPY_CACHE_PATH")
)
sp = Spotify(auth_manager=auth_manager)
```

Add a helper in `spotify_utils.py` that recognizes an expired/revoked refresh
token without printing secrets. The exact exception shape should be verified on
ONL Audio's installed Spotipy version, but likely checks include:

- `SpotifyOauthError`
- `SpotifyException`
- message/body containing `invalid_grant`

Behavior should be:

- log `Spotify authorization expired or invalid; reauthorization is required`
- remove only the configured cache file if it exists
- send an email saying ONL Audio needs interactive Spotify reauthorization
- do not loop retries against the same refresh token

## Manual Reauthorization Shape

After the code has an explicit cache path, the expected recovery flow should be
approximately:

```bash
cd ~/scripts
. "$HOME/scripts/spotify_env.sh"
rm -f "$SPOTIPY_CACHE_PATH"
python3 spotify_auth_smoke_test.py
```

Complete the browser authorization on ONL Audio as the Spotify account that
owns/controls the Outside Spotify device.

## Testing Notes

Before changing production cron behavior:

```bash
cd ~/scripts
. "$HOME/scripts/spotify_env.sh"
python3 connect_outside_spotify.py
python3 stop_outside_spotify.py
tail -n 80 /usr/local/var/log/spotify/spotify.log
```

Only run `connect_outside_spotify.py` when it is acceptable to start playback
on the Outside Spotify device. If testing during a service/event would be
disruptive, use a read-only auth smoke test first:

```bash
cd ~/scripts
. "$HOME/scripts/spotify_env.sh"
python3 spotify_auth_smoke_test.py
```

## Side Risk Found During Repo Scan

The repo currently has credential-like values committed in scripts, including
Spotify and Jira-related shell files. Do not paste them into chat.

Recommended follow-up after the token-expiration fix:

- move secrets out of tracked shell scripts into an ignored local env file
- commit only a `.env.example` / `spotify_env.example.sh`
- rotate exposed Spotify and Jira credentials where possible
- update cron to source the ignored local env file on ONL Audio

## Done Criteria

- ONL Audio has an explicit, documented Spotify token cache path.
- Expired refresh-token failures produce a clear email/log message instead of
  silent cron breakage.
- Manual reauthorization has been tested on ONL Audio.
- Sunday start/stop scripts still work after reauthorization.
- A renewal reminder exists before the next six-month expiration.
