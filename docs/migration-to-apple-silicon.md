# Migration To Apple Silicon

The current 2018 Intel Mac mini is acceptable as the Phase 0 MacOps host. It
should not be treated as the final long-term workstation.

The reason for a future host is not that `ONLAudio` cannot run the current
automations. It can. The reason is that future MacOps work may include
persistent Codex sessions, VS Code Remote SSH, MCP servers, local repository
indexing, `rock-agent`, `Rock-Workbench`, Rock RMS development support,
Python/Node services, multiple background automations, remote desktop sessions,
and future automation experiments.

Do not overload `ONLAudio` with experimental always-running services while it is
still responsible for production-adjacent Spotify and HyperDeck workflows.

## Future Target

Preferred future host:

- Apple Silicon Mac mini, M4 or better preferred
- 24 GB unified memory preferred
- 512 GB internal SSD minimum
- Ethernet
- UPS power
- External SSD, NAS, or media storage as needed

## Migration Goals

- Use `nr-macops` as the source of truth.
- Recreate `/Users/Shared/NR-Workbench` from the bootstrap process.
- Keep secrets out of git and migrate them deliberately.
- Migrate scheduler definitions only after reviewing live behavior.
- Choose one scheduler per automation.
- Preserve known-good Sunday production behavior during the transition.
- Move heavier Codex, MCP, and Rock tooling onto the future host rather than
  expanding `ONLAudio` beyond its Phase 0 role.

## Candidate Future Host

An Apple Silicon Mac mini with at least 24 GB RAM is preferred for the
longer-term Codex/MCP/MacOps workstation.

## Migration Boundary

Until Brad approves a migration step:

- Keep live production scripts in `/Users/northridge/scripts`.
- Keep active cron and launchd definitions unchanged.
- Treat repo scheduler files as templates, not installed config.
- Use documentation and dry runs before changing file-moving automation.
