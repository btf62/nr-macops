#!/usr/bin/env bash
set -euo pipefail

BASE="/Users/Shared/NR-Workbench"

echo "Creating/verifying runtime layout under $BASE"

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
