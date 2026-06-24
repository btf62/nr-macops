# Security

## Repository Rules

Never commit:

- API keys
- passwords
- OAuth tokens
- Spotify credentials
- Rock RMS credentials
- `.env` files
- private production data
- HyperDeck recordings
- raw logs with sensitive content
- large media files

Commit templates and examples only when they are reviewed and contain no
secrets.

## Access Rules

- Do not expose SSH, dashboards, MCP servers, or other control surfaces directly
  to the public internet.
- Avoid unauthenticated web panels.
- Prefer Tailscale or another private network path for remote access.
- Keep live configuration separate from repo-managed templates.
- Use `.env.example` or `config/examples/` for non-secret examples.

## Automation Rules

- Prefer dry-run modes before moving, deleting, renaming, or uploading files.
- Do not alter production cron or launchd jobs without review.
- Do not change Sunday production automation timing without explicit approval.
- Do not modify Blackmagic, NDI, NinjaRMM, Renewed Vision, Rogue Amoeba, or
  other vendor launchd services unless specifically requested.
- Do not edit `spotify_env.sh` or other credential-bearing files without
  explicit approval.
- Do not start experimental always-running MCP, Codex, Rock, Python, or Node
  services on `ONLAudio` without review. Prefer the future Apple Silicon host
  for heavier long-running workloads.
