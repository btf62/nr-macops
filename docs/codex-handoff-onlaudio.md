# Codex Handoff: ONLAudio MacOps / `nr-macops`

Also read: `docs/codex-handoff-onlaudio-addendum.md`

## Context

We are setting up a Northridge MacOps Workbench around the existing Mac mini named `ONLAudio`.

This machine is currently a 2018 Intel Mac mini that already hosts production-adjacent automations for:

- Spotify / outside speaker playlist scheduling
- HyperDeck sync/upload and cleanup
- Blackmagic / NDI / Renewed Vision / Rogue Amoeba support services

A future Apple Silicon Mac mini may replace this machine later, but for now `ONLAudio` is the Phase 0 / prototype MacOps host.

Do not overload `ONLAudio` with experimental always-running services while it
remains responsible for production-adjacent Spotify and HyperDeck workflows.
The long-term target for heavier Codex, MCP, Rock, indexing, and development
workloads is a future Apple Silicon Mac mini.

The goal is to document the current setup, preserve working automations, and gradually move scripts, launchd templates, setup notes, and operational runbooks into a Git repo named:

```text
nr-macops
```

Remote Git URL:

```text
git@github.com:btf62/nr-macops.git
```

## Critical Operating Principle

Do not break currently working Sunday production automations.

Before changing anything:

1. Inventory it.
2. Back it up.
3. Commit documentation/templates to `nr-macops`.
4. Propose changes.
5. Prefer dry-run modes.
6. Avoid destructive actions.

Do not disable cron or launchd jobs until logs and behavior are understood.

---

## Known Host Inventory

Host information gathered from Brad’s terminal session:

```text
Hostname: ONLAudio
User: northridge
Model: Mac mini, Macmini8,1
CPU: 3.2 GHz 6-Core Intel Core i7
RAM: 16 GB
macOS: 15.7.7
Build: 24G720
Internal disk: 466 GiB total, about 263 GiB available
External backup volume: /Volumes/ONL Audio Backups
Backup volume: 1.8 TiB total, about 81 GiB available, 96% full
```

This machine is acceptable as a temporary MacOps host for:

- current Spotify automation
- current HyperDeck automation
- repo development
- SSH / remote desktop
- light Codex work
- light MCP experimentation later

Do not treat it as the final high-capacity long-term MCP/Codex workstation.

---

## Current Scheduling Findings

### User LaunchAgents

Custom Northridge launchd user agents exist at:

```text
/Users/northridge/Library/LaunchAgents/com.northridge.hyperdeck.cleanup.plist
/Users/northridge/Library/LaunchAgents/com.northridge.hyperdeck.master-sync.plist
/Users/northridge/Library/LaunchAgents/com.northridge.hyperdeck.python-sync-smoke.plist
```

`launchctl list | grep -i northridge` showed:

```text
-    0   com.northridge.hyperdeck.python-sync-smoke
-    78  com.northridge.hyperdeck.cleanup
-    78  com.northridge.hyperdeck.master-sync
```

Interpretation:

- `python-sync-smoke` last exited successfully.
- `cleanup` and `master-sync` last exited with status `78`, likely a configuration/software error.
- Do not assume launchd is the currently reliable path until logs are checked.

### HyperDeck LaunchAgent Details

`com.northridge.hyperdeck.master-sync`

```text
Script: /Users/northridge/scripts/hyperdeck_pipeline/bin/master_sync_upload.py
Schedule: Sunday 13:35
WorkingDirectory: /Users/northridge/scripts
Log: /Users/northridge/Library/Logs/hyperdeck/launchd.log
Session type: Aqua
```

`com.northridge.hyperdeck.cleanup`

```text
Script: /Users/northridge/scripts/hyperdeck_pipeline/bin/cleanup_hyperdeck.py --confirm-remote
Schedule: Saturday 23:00
WorkingDirectory: /Users/northridge/scripts
Log: /Users/northridge/Library/Logs/hyperdeck/launchd.log
Session type: Aqua
```

`com.northridge.hyperdeck.python-sync-smoke`

```text
Script: /Users/northridge/scripts/launchd/run_python_sync_smoke_test.sh
No StartCalendarInterval observed
WorkingDirectory: /Users/northridge/scripts
Log: /Users/northridge/Library/Logs/hyperdeck/python-launchd-sync.log
Session type: Aqua
```

### Cron

`crontab -l` showed that cron currently handles Spotify automation and also HyperDeck jobs.

Current cron environment:

```text
SHELL=/bin/bash
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

Spotify cron jobs:

```text
Sunday playlist start: 7:59 AM
Sunday playlist stop: 2:05 PM
Sunday safety stop: 2:15 PM

Dec 23 playlist start: 4:30 PM
Dec 23 playlist stop: 8:15 PM

Dec 24 playlist start: 1:00 PM
Dec 24 playlist stop: 6:30 PM
```

Spotify scripts:

```text
/Users/northridge/scripts/spotify_env.sh
/Users/northridge/scripts/connect_outside_spotify.py
/Users/northridge/scripts/stop_outside_spotify.py
```

Spotify log:

```text
/usr/local/var/log/spotify/cron.log
```

HyperDeck cron jobs:

```text
Sunday sync/upload: Sunday 13:35
Saturday cleanup: Saturday 17:00
```

HyperDeck scripts:

```text
/Users/northridge/scripts/hyperdeck_pipeline/bin/master_sync_upload.py
/Users/northridge/scripts/hyperdeck_pipeline/bin/cleanup_hyperdeck.py --confirm-remote
```

HyperDeck cron log:

```text
/usr/local/var/log/hyperdeck/cron.log
```

Important finding:

```text
HyperDeck master sync/upload appears to be scheduled in BOTH cron and launchd at Sunday 13:35.
```

Do not fix this yet. First inspect logs to confirm what is actually running and succeeding.

---

## Existing System Services

System-level vendor services were observed in:

```text
/Library/LaunchDaemons
/Library/LaunchAgents
```

These include:

- Blackmagic Design Desktop Video / Streaming / Videohub
- NDI
- NinjaRMM
- Renewed Vision / ProPresenter helpers
- Rogue Amoeba audio helper

Do not modify these unless explicitly asked.

---

## Desired Repo Purpose

`nr-macops` should become the source of truth for:

- MacOps documentation
- inventory
- setup checklist
- launchd plist templates
- cron documentation/templates
- HyperDeck scripts or wrappers, when safe to migrate
- Spotify scripts or wrappers, when safe to migrate
- logs/runbook documentation
- future Mac mini migration notes
- future MCP/Codex host setup notes

The repo should not contain:

- API keys
- OAuth tokens
- Spotify credentials
- Rock RMS credentials
- `.env` files
- private production data
- HyperDeck recordings
- logs with sensitive content
- large media files

---

## Desired Repo Structure

Create or update the repo to include:

```text
nr-macops/
  README.md
  docs/
    current-2018-onlaudio-inventory.md
    architecture.md
    setup-checklist.md
    scheduling.md
    hyperdeck-pipeline.md
    spotify-automation.md
    security.md
    remote-access.md
    operations-runbook.md
    migration-to-apple-silicon.md
    codex-handoff-onlaudio.md
  scripts/
    bootstrap/
    hyperdeck/
    spotify/
    maintenance/
    launchd/
    mcp/
  launchd/
    user-agents/
      examples/
  cron/
    examples/
  config/
    examples/
  logs/
    .gitkeep
  tmp/
    .gitkeep
  .gitignore
```

If some of these files/folders already exist, do not overwrite useful content without review.

---

## Desired Local Runtime Layout

Eventually create this runtime structure on ONLAudio or document how to create it:

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

Do not move current working scripts into this structure yet. Create documentation and bootstrap scripts first.

---

## Immediate Codex Tasks

### Task 1: Create/update repo skeleton

In the `nr-macops` repo:

1. Create the documentation and directory skeleton above.
2. Add a conservative `.gitignore`.
3. Add a `README.md` that explains the repo purpose.
4. Add this handoff as:

```text
docs/codex-handoff-onlaudio.md
```

5. Add `docs/current-2018-onlaudio-inventory.md` with the known facts from this handoff.

Do not install launchd jobs yet.

Do not edit the active crontab yet.

Do not move current production scripts yet.

### Task 2: Inventory current scripts and logs

Collect read-only inventory of:

```text
/Users/northridge/scripts/
/Users/northridge/scripts/hyperdeck_pipeline/
/Users/northridge/scripts/hyperdeck_pipeline/bin/
/Users/northridge/scripts/launchd/
/Users/northridge/scripts/*spotify*
/usr/local/var/log/hyperdeck/
/usr/local/var/log/spotify/
/Users/northridge/Library/Logs/hyperdeck/
```

Use commands such as:

```bash
ls -lah /Users/northridge/scripts/
ls -lah /Users/northridge/scripts/hyperdeck_pipeline/
ls -lah /Users/northridge/scripts/hyperdeck_pipeline/bin/
ls -lah /Users/northridge/scripts/launchd/
ls -lah /Users/northridge/scripts/*spotify*
ls -lah /usr/local/var/log/hyperdeck/
ls -lah /usr/local/var/log/spotify/
ls -lah /Users/northridge/Library/Logs/hyperdeck/
```

Then inspect recent logs:

```bash
tail -n 200 /usr/local/var/log/hyperdeck/cron.log
tail -n 200 /Users/northridge/Library/Logs/hyperdeck/launchd.log
tail -n 200 /Users/northridge/Library/Logs/hyperdeck/python-launchd-sync.log
tail -n 200 /usr/local/var/log/spotify/cron.log
```

Summarize findings in:

```text
docs/current-2018-onlaudio-inventory.md
docs/hyperdeck-pipeline.md
docs/spotify-automation.md
```

### Task 3: Preserve current scheduler definitions as templates

Copy current custom scheduler definitions into repo, but sanitize if necessary.

LaunchAgents:

```text
~/Library/LaunchAgents/com.northridge.hyperdeck.cleanup.plist
~/Library/LaunchAgents/com.northridge.hyperdeck.master-sync.plist
~/Library/LaunchAgents/com.northridge.hyperdeck.python-sync-smoke.plist
```

Destination:

```text
launchd/user-agents/
```

Cron:

Export current crontab to a repo template:

```bash
crontab -l > cron/examples/onlaudio-current-crontab.txt
```

Before committing, review for secrets. The current crontab appears to contain paths and schedules, not credentials, but still review.

### Task 4: Build bootstrap script, but do not run destructive actions

Create:

```text
scripts/bootstrap/create_runtime_dirs.sh
```

This script should create the intended `/Users/Shared/NR-Workbench` directory layout.

It should:

- be idempotent
- use `mkdir -p`
- avoid deleting anything
- avoid changing current production scripts
- print what it is doing
- not require root unless necessary

Suggested behavior:

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="/Users/Shared/NR-Workbench"

mkdir -p "$BASE/repos"
mkdir -p "$BASE/automations/hyperdeck"
mkdir -p "$BASE/automations/spotify"
mkdir -p "$BASE/automations/reports"
mkdir -p "$BASE/automations/maintenance"
mkdir -p "$BASE/data/hyperdeck-inbox"
mkdir -p "$BASE/data/hyperdeck-archive"
mkdir -p "$BASE/data/exports"
mkdir -p "$BASE/data/cache"
mkdir -p "$BASE/logs/hyperdeck"
mkdir -p "$BASE/logs/spotify"
mkdir -p "$BASE/logs/codex"
mkdir -p "$BASE/logs/launchd"
mkdir -p "$BASE/logs/maintenance"
mkdir -p "$BASE/secrets"
mkdir -p "$BASE/tmp"

if [ ! -f "$BASE/secrets/README-do-not-commit.txt" ]; then
  cat > "$BASE/secrets/README-do-not-commit.txt" <<'EOF'
This directory is for local secrets only.

Do not commit files from this directory to git.
Do not store secrets in the nr-macops repository.
EOF
fi

echo "Created/verified runtime layout under $BASE"
```

### Task 5: Add safety notes

In `docs/security.md`, document:

- no secrets in git
- no public open SSH
- prefer Tailscale or private network
- separate templates from live config
- dry-run first for file-moving automation
- do not modify vendor launchd services
- do not alter production cron/launchd without review

---

## Known Issues / Questions to Resolve

1. Is HyperDeck currently running successfully from cron, launchd, or both?
2. Why do `com.northridge.hyperdeck.cleanup` and `com.northridge.hyperdeck.master-sync` show last exit status `78`?
3. Should HyperDeck ultimately use cron or launchd, but not both?
4. Should Spotify remain cron-based or move to launchd later?
5. Where should logs live long term?
6. Should current scripts remain in `/Users/northridge/scripts` for now, with repo-managed copies/templates?
7. Does `/Users/Shared/NR-Workbench` already need to be created on ONLAudio, or should it wait until after repo documentation?
8. How full is Time Machine, and are backups completing normally?

---

## Preferred Migration Philosophy

Short term:

- Preserve current working behavior.
- Document everything.
- Add repo-managed templates.
- Do not refactor live automations.

Medium term:

- Choose one scheduler per job.
- Prefer launchd for macOS-native scheduled automation once tested.
- Keep Spotify cron until it is understood and documented.
- Add dry-run and logging improvements.

Long term:

- Migrate to an Apple Silicon Mac mini with 24 GB RAM when available.
- Use `nr-macops` as the source of truth.
- Rebuild runtime layout from documented/bootstrap process.
- Move MacOps services, MCP servers, Codex support, and repo work into the new host.

---

## Guardrails for Codex

Do not do any of the following without explicit Brad approval:

- disable cron jobs
- unload launchd jobs
- delete scripts
- move production scripts
- edit Spotify credentials
- edit `spotify_env.sh`
- delete HyperDeck recordings
- modify Blackmagic, NDI, NinjaRMM, Renewed Vision, or Rogue Amoeba services
- commit secrets
- expose SSH or dashboards to the public internet
- install new always-running services
- start experimental MCP services that could destabilize ONLAudio
- change Sunday production automation timing

When uncertain, create documentation or a proposal instead of changing the live machine.
