# Codex Handoff Addendum: ONLAudio MacOps Future Direction

## Where to Store This File

Save this file in the `nr-macops` repo at:

```text
docs/codex-handoff-onlaudio-addendum.md
```

Then update the main handoff file:

```text
docs/codex-handoff-onlaudio.md
```

Add a short reference near the top:

```markdown
Also read: `docs/codex-handoff-onlaudio-addendum.md`
```

This addendum should be treated as strategic direction and guardrails for the MacOps project. The original handoff remains the operational starting point.

---

# Purpose of This Addendum

Brad has handed off the initial MacOps setup work to Codex on the existing Mac mini named `ONLAudio`.

This addendum clarifies the larger plan:

- `ONLAudio` is the current Phase 0 / prototype host.
- `ONLAudio` is already running useful production-adjacent automation.
- The long-term target is a more suitable Apple Silicon Mac mini.
- The `nr-macops` repo should become the source of truth for scripts, configuration templates, documentation, runbooks, and migration guidance.
- Codex should avoid turning `ONLAudio` into an overloaded experimental box while it remains responsible for Spotify and HyperDeck workflows.

---

# Current State: ONLAudio

`ONLAudio` is currently the working host for:

- Spotify / outside speaker playlist automation
- HyperDeck sync/upload automation
- HyperDeck cleanup automation
- Blackmagic / NDI / Renewed Vision / Rogue Amoeba support services

Known host inventory from Brad’s terminal session:

```text
Hostname: ONLAudio
User: northridge
Model: 2018 Mac mini, Macmini8,1
CPU: 3.2 GHz 6-Core Intel Core i7
RAM: 16 GB
macOS: 15.7.7
Build: 24G720
Internal disk: 466 GiB total, about 263 GiB available
External backup volume: /Volumes/ONL Audio Backups
Backup volume: 1.8 TiB total, about 81 GiB available, 96% full
```

This machine is capable enough for Phase 0 work:

- current Spotify automation
- current HyperDeck automation
- repo development
- SSH
- Screen Sharing
- light VS Code / Codex work
- light MCP experimentation later, if carefully controlled

It should not be treated as the final high-capacity MacOps server.

---

# Future Hardware Direction

The intended long-term host is an Apple Silicon Mac mini, preferably:

```text
M4 or better
24 GB unified memory preferred
512 GB internal SSD minimum
Ethernet
UPS power
External SSD / NAS / media storage as needed
```

The reason for the future machine is not that `ONLAudio` cannot run the current automations. It can.

The reason is that the future MacOps workload may include:

- persistent Codex sessions
- VS Code Remote SSH
- MCP servers
- local repo indexing / search
- `rock-agent`
- `Rock-Workbench`
- Rock RMS development support
- Python / Node services
- multiple background automations
- remote desktop sessions
- future automation experiments
- potentially Docker / OrbStack or similar tooling

Those workloads would benefit from Apple Silicon performance, newer macOS support, and at least 24 GB unified memory.

Do not overload `ONLAudio` with experimental always-running services while it is still responsible for production-adjacent Spotify and HyperDeck workflows.

---

# ChatGPT Project Context

This work belongs in a dedicated ChatGPT Project named something like:

```text
Northridge MacOps Workbench
```

That project should track:

- `ONLAudio` inventory
- `nr-macops` repo decisions
- HyperDeck automation
- Spotify automation
- future Mac mini migration
- Codex usage
- MCP server planning
- `rock-agent` integration
- `Rock-Workbench` integration
- remote access architecture
- safety policies
- runbooks and troubleshooting notes

The ChatGPT Project is for long-running architectural and operational discussion.

The `nr-macops` repo is the source of truth for implementation artifacts:

- scripts
- docs
- templates
- runbooks
- setup checklists
- migration notes

---

# Remote Access Direction

Preferred future remote access stack:

```text
Tailscale
SSH
VS Code Remote SSH
macOS Screen Sharing
Codex on the host
```

Use cases:

- Tailscale: private network access from Brad’s devices
- SSH: terminal/admin/dev access
- VS Code Remote SSH: primary remote development workflow
- macOS Screen Sharing: GUI access when needed
- Codex: agentic work inside the repo/host context

Do not expose SSH, dashboards, MCP servers, or other control surfaces directly to the public internet.

Avoid unauthenticated web panels.

Prefer private-network-only access.

---

# Repo Role and Philosophy

The `nr-macops` repo should be the source of truth for the MacOps environment.

The local filesystem is where things run.

The repo is where the intended configuration, scripts, setup process, runbooks, and migration path live.

Core principle:

```text
Anything that explains, installs, schedules, or automates the Mac mini belongs in nr-macops.
Anything generated, private, temporary, large, or credentialed stays out of git.
```

Commit to the repo:

- documentation
- runbooks
- setup checklists
- bootstrap scripts
- launchd plist templates
- cron examples/templates
- safe wrappers
- test scripts
- `.env.example` files
- migration notes

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
- large media files
- generated exports unless explicitly approved

---

# Desired Repo Locations

Store the main handoff at:

```text
docs/codex-handoff-onlaudio.md
```

Store this addendum at:

```text
docs/codex-handoff-onlaudio-addendum.md
```

Store current machine inventory at:

```text
docs/current-2018-onlaudio-inventory.md
```

Store future migration notes at:

```text
docs/migration-to-apple-silicon.md
```

Store remote access notes at:

```text
docs/remote-access.md
```

Store security and secrets policy at:

```text
docs/security.md
```

Store scheduler documentation at:

```text
docs/scheduling.md
```

Store HyperDeck documentation at:

```text
docs/hyperdeck-pipeline.md
```

Store Spotify documentation at:

```text
docs/spotify-automation.md
```

Store launchd templates at:

```text
launchd/user-agents/
```

Store cron examples at:

```text
cron/examples/
```

Store bootstrap scripts at:

```text
scripts/bootstrap/
```

Store future HyperDeck scripts or wrappers at:

```text
scripts/hyperdeck/
```

Store future Spotify scripts or wrappers at:

```text
scripts/spotify/
```

---

# Recommended `nr-macops` Repo Structure

Target structure:

```text
nr-macops/
  README.md
  docs/
    codex-handoff-onlaudio.md
    codex-handoff-onlaudio-addendum.md
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

Do not overwrite useful existing content without review.

---

# Desired Runtime Layout

Eventually create or document this runtime structure on `ONLAudio` and later on the future Apple Silicon Mac mini:

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

Do not move current working scripts into this structure until the current behavior is documented and Brad approves the migration.

---

# Current Scheduling Findings to Preserve

## Cron

`crontab -l` showed that cron currently handles Spotify automation and also HyperDeck jobs.

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

## launchd

Custom Northridge LaunchAgents:

```text
/Users/northridge/Library/LaunchAgents/com.northridge.hyperdeck.cleanup.plist
/Users/northridge/Library/LaunchAgents/com.northridge.hyperdeck.master-sync.plist
/Users/northridge/Library/LaunchAgents/com.northridge.hyperdeck.python-sync-smoke.plist
```

Observed `launchctl` status:

```text
-    0   com.northridge.hyperdeck.python-sync-smoke
-    78  com.northridge.hyperdeck.cleanup
-    78  com.northridge.hyperdeck.master-sync
```

Interpretation:

- `python-sync-smoke` last exited successfully.
- `cleanup` and `master-sync` last exited with status `78`, likely a configuration/software error.
- Do not assume launchd is the reliable active path until logs are reviewed.

## Duplicate Scheduling Concern

Important finding:

```text
HyperDeck master sync/upload appears to be scheduled in BOTH cron and launchd at Sunday 13:35.
```

Do not fix this immediately.

First inspect logs and determine what is actually running and succeeding.

---

# Known Questions to Resolve

1. Is HyperDeck currently running successfully from cron, launchd, or both?
2. Why do `com.northridge.hyperdeck.cleanup` and `com.northridge.hyperdeck.master-sync` show last exit status `78`?
3. Should HyperDeck ultimately use cron or launchd, but not both?
4. Should Spotify remain cron-based or move to launchd later?
5. Where should logs live long term?
6. Should current scripts remain in `/Users/northridge/scripts` for now, with repo-managed copies/templates?
7. When should `/Users/Shared/NR-Workbench` be created on `ONLAudio`?
8. Are Time Machine backups completing correctly despite the backup drive being 96% full?
9. Which future MCP servers should run locally, and which should wait for the Apple Silicon machine?
10. What is the safe boundary between production automation and experimental Codex/MCP work?

---

# Immediate Codex Guidance

If this file is dropped into Codex on `ONLAudio`, do the following:

1. Add this file to:

```text
docs/codex-handoff-onlaudio-addendum.md
```

2. Update:

```text
docs/codex-handoff-onlaudio.md
```

Add a reference near the top:

```markdown
Also read: `docs/codex-handoff-onlaudio-addendum.md`
```

3. Update or create:

```text
docs/migration-to-apple-silicon.md
```

Summarize the future hardware direction:

```text
Future target: Apple Silicon Mac mini, preferably M4 or better, 24 GB RAM, 512 GB SSD minimum, Ethernet, UPS, external media storage as needed.
```

4. Update or create:

```text
docs/remote-access.md
```

Include the preferred remote access stack:

```text
Tailscale
SSH
VS Code Remote SSH
macOS Screen Sharing
Codex on host
```

5. Update or create:

```text
docs/security.md
```

Include the warning:

```text
Do not expose SSH, dashboards, MCP servers, or other control surfaces directly to the public internet.
```

6. Update or create:

```text
docs/current-2018-onlaudio-inventory.md
```

Make clear that `ONLAudio` is a Phase 0 host, not the final long-term MacOps machine.

---

# Guardrails for Codex

Do not do any of the following without explicit Brad approval:

- disable cron jobs
- unload launchd jobs
- delete scripts
- move production scripts
- edit Spotify credentials
- edit `spotify_env.sh`
- delete HyperDeck recordings
- modify Blackmagic services
- modify NDI services
- modify NinjaRMM services
- modify Renewed Vision services
- modify Rogue Amoeba services
- commit secrets
- expose SSH or dashboards to the public internet
- install new always-running services
- change Sunday production automation timing
- start experimental MCP services that could destabilize ONLAudio
- convert cron to launchd before logs are reviewed

When uncertain, document findings or propose a plan instead of changing the live machine.

---

# Practical Next Step

Codex should now make the repo documentation more complete, not refactor live automation.

Preferred next action:

```text
Read docs/codex-handoff-onlaudio.md and docs/codex-handoff-onlaudio-addendum.md. Update the repo documentation to reflect ONLAudio as the Phase 0 host and Apple Silicon Mac mini as the future target. Do not change active cron jobs, launchd jobs, or production scripts.
```

After that, Codex can continue with safe inventory and documentation work.
