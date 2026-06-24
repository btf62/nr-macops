# Codex Handoff: Northridge MacOps / RockOps Mac Mini

## Purpose

We are setting up an always-on Mac mini to serve as a controlled operations and development workstation for Northridge Church.

This machine will support:

- media automation, especially HyperDeck recording movement, cleanup, and organization
- scheduled audio / Spotify workflows for parking lot or outside speakers
- Rock RMS development support
- local repos for `rock-agent`, `Rock-Workbench`, and related tooling
- MCP servers used by AI agents
- a stable Codex environment reachable remotely
- scheduled maintenance and reporting tasks

This Mac mini should be treated as lightweight church infrastructure, not a casual personal desktop.

## Primary Goals

1. Create a clean, documented filesystem layout.
2. Create a dedicated repo for server configuration and automation scripts.
3. Keep all scripts version-controlled.
4. Keep secrets out of git.
5. Prefer safe, testable, dry-run-capable automation.
6. Use macOS-native scheduling where appropriate, especially `launchd`.
7. Keep a clear separation between development work and production automation.
8. Make the environment understandable to Brad and future maintainers.

## Proposed Repo Name

Use:

```text
nr-macops
```

This repo should contain the configuration, scripts, documentation, and setup guidance for this Mac mini.

## Proposed Local Filesystem Layout

Create or document this structure:

```text
/Users/Shared/NR-Workbench/
  repos/
    nr-macops/
    rock-agent/
    Rock-Workbench/
  automations/
    hyperdeck/
    spotify/
    reports/
    maintenance/
  data/
    hyperdeck-inbox/
    hyperdeck-archive/
    exports/
    cache/
  logs/
    hyperdeck/
    spotify/
    codex/
    launchd/
    maintenance/
  secrets/
    README-do-not-commit.txt
  tmp/
```

The `repos/` folder contains git repositories.

The `automations/` folder may contain checked-out scripts, wrappers, or symlinks used by scheduled jobs.

The `data/` folder contains operational working files.

The `logs/` folder contains runtime logs.

The `secrets/` folder is local-only and must never be committed to git.

The `tmp/` folder is for temporary files.

## Proposed Repo Structure

Inside `nr-macops`, create:

```text
nr-macops/
  README.md
  docs/
    architecture.md
    setup-checklist.md
    security.md
    codex-handoff.md
    operations-runbook.md
    remote-access.md
  scripts/
    bootstrap/
    hyperdeck/
    spotify/
    maintenance/
    rock/
    mcp/
  launchd/
    user-agents/
    daemons/
    examples/
  config/
    examples/
  tests/
  logs/
    .gitkeep
  tmp/
    .gitkeep
  .gitignore
```

## Important Rules

Do not commit:

- API keys
- passwords
- OAuth tokens
- Spotify credentials
- Rock RMS credentials
- `.env` files
- private production data
- HyperDeck recordings
- logs with sensitive content
- generated exports unless specifically approved

Do commit:

- scripts
- docs
- setup checklists
- launchd templates
- `.env.example` files
- dry-run examples
- README instructions
- test fixtures that contain no private data

## Automation Safety Requirements

All file-moving or file-deleting scripts should support:

```bash
--dry-run
--verbose
--source
--destination
--max-age
```

Destructive scripts should not run unless explicitly configured.

Any script that deletes, moves, archives, or overwrites files should log:

- timestamp
- source path
- destination path
- action taken
- whether dry-run was enabled
- errors encountered

Default behavior should be conservative.

## launchd Guidance

Use `launchd` for scheduled macOS jobs.

Store launchd plist templates in the repo under:

```text
launchd/user-agents/
launchd/daemons/
```

Do not install them automatically until reviewed.

Provide installation commands in documentation, for example:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.northridge.example.plist
launchctl kickstart -k gui/$(id -u)/com.northridge.example
launchctl print gui/$(id -u)/com.northridge.example
```

Use user agents for user-context tasks such as Spotify/audio automation.

Use daemons only when root/system-level behavior is truly necessary.

## Development Setup

The Mac mini should support:

- Homebrew
- Git
- GitHub CLI
- Python 3
- Node.js / npm
- VS Code Remote SSH
- Codex CLI
- MCP server tooling
- optional Docker or OrbStack if needed later

Do not assume Docker is required until a specific workflow needs it.

## Remote Access Assumptions

Preferred remote access stack:

- Tailscale for private network access
- SSH for terminal and development workflows
- VS Code Remote SSH for coding
- macOS Screen Sharing for GUI access
- optional HDMI dummy plug if headless display behavior is poor

Do not expose SSH, dashboards, or control panels directly to the public internet.

## Initial Codex Task

First task:

Create the `nr-macops` repo skeleton, documentation files, `.gitignore`, and a bootstrap script that creates the intended local folder structure.

Do not install launchd jobs yet.

Do not move real HyperDeck files yet.

Do not configure Spotify automation yet.

Do not touch production Rock RMS data.

After creating the skeleton, summarize:

1. What files were created.
2. What assumptions were made.
3. What needs Brad’s review before proceeding.
4. Recommended next steps.
