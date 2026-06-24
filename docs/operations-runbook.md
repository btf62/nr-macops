# Operations Runbook

## Before Changing Automation

1. Confirm the live scheduler path.
2. Review recent logs.
3. Back up current config or script text.
4. Commit repo documentation or templates.
5. Prefer dry-run testing.
6. Make one small reviewed change at a time.

## Current High-Risk Areas

- HyperDeck sync/upload is scheduled in both cron and launchd.
- `com.northridge.hyperdeck.cleanup` and
  `com.northridge.hyperdeck.master-sync` show launchd status `78`.
- Time Machine backup volume is reported 96% full.
- `ONLAudio` is both the Phase 0 workbench and the current automation host, so
  experimental always-on services should not be added casually.

## Host Direction

- Treat `ONLAudio` as the Phase 0 host for current Spotify and HyperDeck
  automation, inventory, documentation, and light Codex work.
- Treat the future Apple Silicon Mac mini as the long-term target for heavier
  Codex, MCP, Rock, indexing, Python/Node, and automation experiments.
- When uncertain, document findings or propose a plan instead of changing the
  live machine.

## Useful Read-Only Checks

```bash
crontab -l
launchctl list | grep -i northridge
tail -n 200 /usr/local/var/log/hyperdeck/cron.log
tail -n 200 /usr/local/var/log/spotify/cron.log
tail -n 200 /Users/northridge/Library/Logs/hyperdeck/launchd.log
```
