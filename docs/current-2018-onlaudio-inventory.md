# Current 2018 ONLAudio Inventory

Last reviewed: 2026-06-24.

This document records observed state for the current Phase 0 MacOps host. It is
inventory, not a change plan.

`ONLAudio` is the prototype host for preserving and documenting current
automation. It is not the final long-term MacOps workstation. The intended
long-term target is a future Apple Silicon Mac mini that can carry heavier
Codex, MCP, Rock, indexing, and development workloads.

## Host

- Hostname: `ONLAudio`
- User: `northridge`
- Model: Mac mini, `Macmini8,1`
- CPU: 3.2 GHz 6-Core Intel Core i7
- RAM: 16 GB
- macOS: 15.7.7
- Build: 24G720
- Internal disk: 466 GiB total, about 263 GiB available
- External backup volume: `/Volumes/ONL Audio Backups`
- Backup volume: 1.8 TiB total, about 81 GiB available, 96% full

## Current Roles

- Spotify / outside speaker playlist scheduling
- HyperDeck sync, rename, upload, and cleanup
- Blackmagic / NDI / Renewed Vision / Rogue Amoeba support services
- Temporary MacOps repo development and Codex work

## Phase 0 Boundary

Appropriate Phase 0 use:

- Keep current Spotify automation stable.
- Keep current HyperDeck automation stable.
- Continue repo development and documentation.
- Use SSH, Screen Sharing, and light Codex work carefully.
- Collect read-only inventory and logs.

Avoid on `ONLAudio` unless Brad approves:

- Persistent experimental MCP servers.
- Heavy local indexing or background development services.
- Docker / OrbStack or similar always-running infrastructure.
- Production scheduler refactors before logs and behavior are understood.

## Current Script Inventory

Observed `/Users/northridge/scripts/` contains:

- Spotify automation: `spotify_env.sh`, `connect_outside_spotify.py`,
  `stop_outside_spotify.py`, `spotify_utils.py`
- HyperDeck helpers: `hyperdeck_diag.sh`, `hyperdeck_network_poc.py`,
  `hyperdeck_sync_python_test.sh`, `master_sync_upload_python_test.sh`
- HyperDeck pipeline directory: `hyperdeck_pipeline/`
- launchd helper directory: `launchd/`
- scheduler/reference files: `cron.tab.onlaudio`, `cron.tab.onlgraphics`,
  `install_hyperdeck_launchd.sh`, `uninstall_hyperdeck_launchd.sh`,
  `northridge-newsyslog.conf`

Observed `/Users/northridge/scripts/hyperdeck_pipeline/bin/` contains:

- `cleanup_hyperdeck.py`
- `copy_to_gdrive.py`
- `hyperdeck_ftp_diag.py`
- `hyperdeck_sync.py`
- `master_sync_upload.py`
- `pipeline_config.py`
- `rename_files.py`

Observed `/Users/northridge/scripts/launchd/` contains:

- `README.md`
- `com.northridge.hyperdeck.cleanup.plist`
- `com.northridge.hyperdeck.master-sync.plist`
- `com.northridge.hyperdeck.python-sync-smoke.plist`
- `run_python_sync_smoke_test.sh`

## Current Logs

Observed log locations:

- `/usr/local/var/log/hyperdeck/cron.log`
- `/usr/local/var/log/hyperdeck/sync_upload.log`
- `/usr/local/var/log/hyperdeck/launchd.log`
- `/usr/local/var/log/spotify/cron.log`
- `/usr/local/var/log/spotify/spotify.log`
- `/Users/northridge/Library/Logs/hyperdeck/launchd.log`
- `/Users/northridge/Library/Logs/hyperdeck/python-launchd-sync.log`

Log sizes on 2026-06-24:

- HyperDeck cron log: about 13 MB, last updated 2026-06-21 14:20
- HyperDeck sync/upload log: about 286 KB, last updated 2026-06-21 14:20
- Spotify cron log: about 64 KB, last updated 2026-06-21 14:15
- Spotify app log: about 190 KB, last updated 2026-06-21 14:15
- User launchd log: current visible file only shows newsyslog rollover on
  2026-04-03 01:30
- Python launchd smoke log: about 5.7 KB, last updated 2026-04-01 20:31

## Scheduler State

Current custom user LaunchAgents:

- `com.northridge.hyperdeck.cleanup`
- `com.northridge.hyperdeck.master-sync`
- `com.northridge.hyperdeck.python-sync-smoke`

Observed `launchctl list | grep -i northridge` on 2026-06-24:

```text
- 0  com.northridge.hyperdeck.python-sync-smoke
- 78 com.northridge.hyperdeck.cleanup
- 78 com.northridge.hyperdeck.master-sync
```

Cron also schedules Spotify and HyperDeck jobs. The current crontab is
preserved at `cron/examples/onlaudio-current-crontab.txt`.

Important duplicate scheduling finding:

- HyperDeck master sync/upload is scheduled in both cron and launchd for Sunday
  13:35.
- Do not resolve this yet. Logs currently suggest cron is the successful path.

## Recent Log Findings

HyperDeck cron appears active and successful:

- Saturday cleanup completed on 2026-06-20 at 17:00.
- Sunday sync/upload started on 2026-06-21 at 13:35.
- HD1 transferred 4 files, HD2 transferred 2 files.
- Rename completed for both HyperDeck sources.
- Upload to Google Drive completed on 2026-06-21 at 14:20.
- Email summary was attempted/sent by the pipeline.

Spotify cron appears active and successful:

- Sunday start completed on 2026-06-21 at 07:59.
- Sunday stop completed on 2026-06-21 at 14:05.
- Sunday safety stop completed on 2026-06-21 at 14:15.
- Logs show recurring `urllib3` LibreSSL warnings, but the flows continued.

Launchd status is still unresolved:

- `python-sync-smoke` last exit status is `0` and its log shows dry-run sync
  activity on 2026-04-01.
- `cleanup` and `master-sync` show last exit status `78`.
- The current user launchd log only shows rotation. Rotated logs include older
  HyperDeck output but do not yet explain the current status `78`.

## Do Not Change Yet

- Active crontab
- Active LaunchAgents
- Production scripts under `/Users/northridge/scripts`
- Spotify credentials or `spotify_env.sh`
- HyperDeck recordings or download/archive directories
- Vendor services under `/Library/LaunchDaemons` or `/Library/LaunchAgents`
- Always-running experimental services that could destabilize `ONLAudio`
