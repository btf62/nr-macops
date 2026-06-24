# Setup Checklist

## Phase 0: Documentation Only

- [x] Create repo skeleton.
- [x] Add conservative `.gitignore`.
- [x] Preserve current cron as a repo template.
- [x] Preserve current custom HyperDeck LaunchAgents as repo templates.
- [x] Add safe runtime directory bootstrap script.
- [x] Document that `ONLAudio` is the Phase 0 host.
- [x] Document Apple Silicon Mac mini as the long-term target.
- [ ] Continue reviewing logs to explain launchd status `78`.
- [ ] Decide whether HyperDeck should ultimately use cron or launchd.
- [ ] Decide which future MCP/Codex/Rock services belong on `ONLAudio`, if any,
  and which should wait for the Apple Silicon host.

## Future Host Bootstrap

- [ ] Clone `nr-macops`.
- [ ] Review `docs/security.md`.
- [ ] Run `scripts/bootstrap/create_runtime_dirs.sh` only after confirming the
  target host and path.
- [ ] Copy or migrate scripts only after live behavior is fully documented.
- [ ] Install scheduler definitions only after review.
- [ ] Move heavier Codex, MCP, and Rock workflows to the future Apple Silicon
  Mac mini when available.
