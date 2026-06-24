# nr-macops

Northridge MacOps Workbench documentation and setup repository.

This repo is the source of truth for documenting and gradually migrating the
production-adjacent automations currently running on the 2018 Intel Mac mini
named `ONLAudio`.

`ONLAudio` is the Phase 0 / prototype MacOps host. It is capable enough for the
current Spotify and HyperDeck workflows, repo development, SSH, Screen Sharing,
and light Codex work. It should not be treated as the final high-capacity
MacOps, MCP, Codex, or Rock development workstation.

The long-term target is a more suitable Apple Silicon Mac mini. The future host
should take over heavier always-on workloads such as persistent Codex sessions,
MCP servers, Rock tooling, local indexing, Python/Node services, and future
automation experiments once the current production behavior is fully documented.

Current focus:

- inventory the live host before changing behavior
- preserve scheduler definitions as reviewed templates
- document Spotify and HyperDeck automation
- keep secrets, logs, media files, and private operational data out of git
- prepare a safe future runtime layout under `/Users/Shared/NR-Workbench`
- preserve a migration path from `ONLAudio` to the future Apple Silicon host

This repo is intentionally conservative. Do not modify active cron jobs,
launchd jobs, production scripts, vendor services, credentials, recordings, or
Sunday automation timing without explicit review and approval. Do not overload
`ONLAudio` with experimental always-running services while it remains
responsible for production-adjacent automation.

## Repo Layout

```text
docs/                  MacOps documentation and runbooks
scripts/bootstrap/     Safe setup helpers
scripts/hyperdeck/     Future repo-managed HyperDeck scripts or wrappers
scripts/spotify/       Future repo-managed Spotify scripts or wrappers
scripts/maintenance/   Future maintenance scripts
scripts/launchd/       Future launchd helper scripts
scripts/mcp/           Future MCP/Codex host helpers
launchd/user-agents/   Preserved and future launchd user-agent templates
cron/examples/         Preserved cron templates
config/examples/       Non-secret configuration examples
logs/                  Placeholder only; runtime logs are ignored
tmp/                   Placeholder only; temporary files are ignored
```

Start with:

- `docs/codex-handoff-onlaudio.md`
- `docs/codex-handoff-onlaudio-addendum.md`
- `docs/current-2018-onlaudio-inventory.md`
- `docs/migration-to-apple-silicon.md`
- `docs/scheduling.md`
- `docs/hyperdeck-pipeline.md`
- `docs/spotify-automation.md`
- `docs/security.md`
