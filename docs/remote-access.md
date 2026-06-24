# Remote Access

Preferred remote access model:

- Tailscale or private network first.
- SSH for terminal access.
- VS Code Remote SSH for code work.
- macOS Screen Sharing for GUI access when needed.
- Codex on the host for repo-aware work.
- Optional HDMI dummy plug if headless display behavior is unreliable.

Use `ONLAudio` conservatively while it remains the Phase 0 automation host.
Remote access should support inventory, documentation, and light Codex work, not
unreviewed always-on experimental services.

Do not expose SSH, dashboards, MCP servers, or other control surfaces directly
to the public internet. Avoid unauthenticated web panels and prefer
private-network-only access.

The future Apple Silicon Mac mini should become the better target for heavier
remote development, persistent Codex sessions, MCP servers, and Rock tooling.
