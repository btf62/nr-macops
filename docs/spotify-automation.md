# Spotify Automation

Last reviewed: 2026-06-24.

## Live Runtime

Current Spotify scripts live under:

```text
/Users/northridge/scripts/
```

Observed files:

- `spotify_env.sh`
- `connect_outside_spotify.py`
- `stop_outside_spotify.py`
- `spotify_utils.py`

Do not edit `spotify_env.sh` or other production scripts yet.

## Current Cron Schedule

- Sunday playlist start: 07:59
- Sunday playlist stop: 14:05
- Sunday safety stop: 14:15
- December 23 playlist start: 16:30
- December 23 playlist stop: 20:15
- December 24 playlist start: 13:00
- December 24 playlist stop: 18:30

Logs:

- `/usr/local/var/log/spotify/cron.log`
- `/usr/local/var/log/spotify/spotify.log`

## Recent Evidence

Recent cron logs show successful Sunday start/stop flows through 2026-06-21.
The automation transfers playback to `Outside Spotify`, sets volume, starts the
configured playlist, pauses playback at stop time, and sends email summaries.

The logs also show a recurring `urllib3` warning because the system Python SSL
module is compiled with LibreSSL. This warning has not prevented the observed
flows from completing.

## Open Questions

- Should Spotify remain cron-based or move to launchd later?
- Should the Python environment be made more explicit to avoid library warnings?
- Where should long-term Spotify logs live?
