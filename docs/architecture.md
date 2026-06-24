# Architecture

`nr-macops` documents and prepares the MacOps environment for Northridge.

The current host, `ONLAudio`, remains the live automation machine. This repo is
not yet the runtime location for production scripts.

`ONLAudio` is the Phase 0 host: useful, active, and intentionally protected. It
should remain focused on known-good Spotify and HyperDeck behavior while the
repo captures inventory, templates, runbooks, and migration guidance.

The long-term target is an Apple Silicon Mac mini that can carry heavier
MacOps, MCP, Codex, Rock tooling, indexing, and development workloads.

## Current State

- Live scripts are under `/Users/northridge/scripts`.
- Cron currently runs Spotify and HyperDeck automations.
- launchd has repo-captured HyperDeck user-agent templates, but two active
  HyperDeck agents currently show last exit status `78`.
- Logs are split between `/usr/local/var/log/...` and
  `/Users/northridge/Library/Logs/...`.
- Always-on experimental MCP/Codex/Rock services should wait until there is a
  reviewed plan, and may be better suited for the future Apple Silicon host.

## Host Roles

Phase 0, `ONLAudio`:

- Keep current Spotify and HyperDeck automation stable.
- Support repo development and light Codex work.
- Provide read-only inventory and documentation for migration.

Long-term, Apple Silicon Mac mini:

- Run persistent Codex and MCP workloads.
- Support VS Code Remote SSH and Rock development workflows.
- Host future Python/Node automations after review.
- Provide a clean rebuild target from `nr-macops` documentation and scripts.

## Intended Future Runtime Layout

```text
/Users/Shared/NR-Workbench/
  repos/
  automations/
  data/
  logs/
  secrets/
  tmp/
```

Use `scripts/bootstrap/create_runtime_dirs.sh` to create the directory layout
when ready. The bootstrap script does not move or modify live automations.

## Operating Principle

Inventory first, preserve current behavior, then migrate deliberately.
