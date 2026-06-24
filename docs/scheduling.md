# Scheduling

Last reviewed: 2026-06-24.

## Cron

Current crontab is preserved at:

```text
cron/examples/onlaudio-current-crontab.txt
```

Cron currently defines:

- Spotify Sunday playlist start at 07:59.
- Spotify Sunday playlist stop at 14:05.
- Spotify Sunday safety stop at 14:15.
- Spotify December 23 start/stop.
- Spotify December 24 start/stop.
- HyperDeck Sunday sync/upload at 13:35.
- HyperDeck Saturday cleanup at 17:00.

Do not edit active cron until the production behavior has been reviewed.

## launchd

Current custom user LaunchAgents are preserved under:

```text
launchd/user-agents/
```

Observed user agents:

- `com.northridge.hyperdeck.cleanup`
- `com.northridge.hyperdeck.master-sync`
- `com.northridge.hyperdeck.python-sync-smoke`

Observed status on 2026-06-24:

```text
- 0  com.northridge.hyperdeck.python-sync-smoke
- 78 com.northridge.hyperdeck.cleanup
- 78 com.northridge.hyperdeck.master-sync
```

The status `78` needs investigation before using launchd as the trusted path.

## Duplicate Scheduling Risk

HyperDeck Sunday sync/upload appears in both cron and launchd at 13:35. Do not
change either scheduler yet. Current logs suggest cron is completing the Sunday
pipeline successfully.
