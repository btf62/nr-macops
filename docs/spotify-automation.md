# Spotify Automation

Last reviewed: 2026-06-30.

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

Repo-managed copies now live under:

```text
scripts/spotify/
```

The live runtime still uses `/Users/northridge/scripts/` until an explicit
cutover is reviewed and tested. Do not commit the live `spotify_env.sh`; use
`config/examples/spotify_env.example.sh` as the non-secret template.

## Spotify Refresh Token Expiration

Spotify Developer refresh tokens begin expiring under the 2026 policy change
on 2026-07-20. The runtime scripts were updated on ONL Audio on 2026-06-30 to:

- use an explicit `SPOTIPY_CACHE_PATH`
- centralize `SpotifyOAuth` setup in `spotify_utils.py`
- detect `invalid_grant` / OAuth failures
- remove only the configured cache file when reauthorization is required
- send a clear reauthorization-required email
- provide `spotify_auth_smoke_test.py` for read-only authorization checks

The configured ONL Audio cache path is:

```text
$HOME/.cache-northridge-outside-spotify-token.json
```

The current valid Spotipy cache was copied into that path on 2026-06-30 so the
new explicit path would not break cron before the planned fresh reauthorization.
Run `scripts/spotify/spotify_auth_smoke_test.py` interactively when performing
reauthorization.

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
