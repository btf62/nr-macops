#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SCRIPT_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DEST="/tmp/hyperdeck_python_master_test"
DEFAULT_LOG_FILE="/usr/local/var/log/hyperdeck/sync_upload.log"
PYTHON_MASTER="$SCRIPT_HOME/hyperdeck_pipeline/bin/master_sync_upload.py"

DEST_DIR="$DEFAULT_DEST"
SYNC_DRY_RUN=false
WITH_UPLOAD=false
MIN_FREE_GB=120
EXTRA_ARGS=()

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

log_and_stdout() {
  local msg="[$(timestamp)] [master_sync_upload_python_test.sh] $1"
  echo "$msg" | tee -a "$DEFAULT_LOG_FILE"
}

bytes_from_gb() {
  local gb="$1"
  echo $((gb * 1024 * 1024 * 1024))
}

free_bytes_for_path() {
  local path="$1"
  mkdir -p "$path"
  df -Pk "$path" | awk 'NR==2 {print $4 * 1024}'
}

usage() {
  cat <<'EOF'
Usage: ./master_sync_upload_python_test.sh [options]

Options:
  --dest DIR         Destination root for Python sync output
  --sync-dry-run     Run the Python sync in dry-run mode
  --with-upload      Enable the Python upload step after rename
  --min-free-gb N    Require at least N GiB free before real syncs (default: 120)
  --help             Show this help

Defaults:
  - Destination: /tmp/hyperdeck_python_master_test
  - Upload: skipped
  - Email: disabled
  - Minimum free space for real syncs: 120 GiB
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      DEST_DIR="${2:?--dest requires a path}"
      shift 2
      ;;
    --sync-dry-run)
      SYNC_DRY_RUN=true
      shift
      ;;
    --with-upload)
      WITH_UPLOAD=true
      shift
      ;;
    --min-free-gb)
      MIN_FREE_GB="${2:?--min-free-gb requires an integer}"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$SYNC_DRY_RUN" == false ]]; then
  required_bytes=$(bytes_from_gb "$MIN_FREE_GB")
  free_bytes=$(free_bytes_for_path "$DEST_DIR")
  if (( free_bytes < required_bytes )); then
    log_and_stdout "❌ Refusing to start real sync: only $((free_bytes / 1024 / 1024 / 1024)) GiB free at $DEST_DIR, require at least ${MIN_FREE_GB} GiB."
    exit 1
  fi
fi

cmd=(
  python3
  "$PYTHON_MASTER"
  --dest "$DEST_DIR"
  --log-file "$DEFAULT_LOG_FILE"
  --no-email
)

if [[ "$WITH_UPLOAD" == false ]]; then
  cmd+=(--no-upload)
fi

if [[ "$SYNC_DRY_RUN" == true ]]; then
  cmd+=(--sync-dry-run)
  if [[ "$WITH_UPLOAD" == true ]]; then
    cmd+=(--upload-dry-run)
  fi
fi

exec "${cmd[@]}"
