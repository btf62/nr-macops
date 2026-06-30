#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SYNC="$SCRIPT_DIR/hyperdeck_pipeline/bin/hyperdeck_sync.py"
TEST_DEST_ROOT="${HYPERDECK_PYTHON_TEST_DEST:-/tmp/hyperdeck_python_test}"
TEST_LOG_FILE="${HYPERDECK_PYTHON_TEST_LOG:-/tmp/hyperdeck_python_sync.log}"

usage() {
  echo "Usage: $0 <HyperDeck IP or name> [--sync-while-recording] [--dry-run]"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

mkdir -p "$TEST_DEST_ROOT"
touch "$TEST_LOG_FILE"

if [[ $# -gt 1 ]]; then
  EXTRA_ARGS=("${@:2}")
else
  EXTRA_ARGS=()
fi

CMD=(python3 "$PYTHON_SYNC" "$1" "$TEST_DEST_ROOT")
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi
CMD+=(--log-file "$TEST_LOG_FILE")

exec "${CMD[@]}"
