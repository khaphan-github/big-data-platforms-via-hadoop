#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ACTION="${1:-all}"

case "$ACTION" in
  all)
    "$SCRIPT_DIR/01_generate_mock_data.sh"
    "$SCRIPT_DIR/02_run_job.sh"
    ;;
  setup)
    "$SCRIPT_DIR/01_generate_mock_data.sh"
    ;;
  run)
    "$SCRIPT_DIR/02_run_job.sh"
    ;;
  cleanup)
    "$SCRIPT_DIR/03_cleanup.sh"
    ;;
  *)
    echo "Usage: $0 [all|setup|run|cleanup]"
    exit 1
    ;;
esac
