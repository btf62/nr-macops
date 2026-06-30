# HyperDeck Pipeline

Last reviewed: 2026-06-30.

## Live Runtime

Current production-adjacent scripts live under:

```text
/Users/northridge/scripts/hyperdeck_pipeline/
```

Important bin scripts:

- `master_sync_upload.py`
- `hyperdeck_sync.py`
- `rename_files.py`
- `copy_to_gdrive.py`
- `cleanup_hyperdeck.py`
- `pipeline_config.py`

Repo-managed copies now live under:

```text
scripts/hyperdeck/hyperdeck_pipeline/
```

The live runtime still uses `/Users/northridge/scripts/hyperdeck_pipeline/`
until an explicit cutover is reviewed and tested. The copied test wrappers in
`scripts/hyperdeck/` resolve their local repo path, but active cron still points
at the existing production location.

## Current Cron Schedule

- Sunday sync/upload: Sunday 13:35
- Saturday cleanup: Saturday 17:00

Logs:

- `/usr/local/var/log/hyperdeck/cron.log`
- `/usr/local/var/log/hyperdeck/sync_upload.log`

## Current launchd Templates

Preserved templates:

- `launchd/user-agents/com.northridge.hyperdeck.master-sync.plist`
- `launchd/user-agents/com.northridge.hyperdeck.cleanup.plist`
- `launchd/user-agents/com.northridge.hyperdeck.python-sync-smoke.plist`

The live `master-sync` and `cleanup` agents show last exit status `78`; do not
rely on launchd until this is understood.

## Recent Evidence

Recent cron logs show:

- Cleanup completed on 2026-06-20 at 17:00.
- Sync/upload started on 2026-06-21 at 13:35.
- HD1 transferred 4 files.
- HD2 transferred 2 files.
- Rename completed.
- Upload to Google Drive completed on 2026-06-21 at 14:20.

## Open Questions

- Is cron the only currently successful production path?
- Why do the launchd agents report status `78`?
- Should HyperDeck ultimately use cron or launchd, but not both?
- Where should long-term logs live?
