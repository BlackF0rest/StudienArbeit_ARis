#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
UI_DIR="${REPO_ROOT}/Software/Onboard_UI"

log() {
  printf '[update_onboard] %s\n' "$1"
}

require_tools() {
  local missing=()
  for tool in git npm systemctl; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      missing+=("${tool}")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    log "Missing required tools: ${missing[*]}"
    exit 1
  fi
}

update_repo() {
  log "Pulling latest git changes..."
  git -C "${REPO_ROOT}" pull --ff-only
}

rebuild_ui() {
  log "Rebuilding Onboard_UI..."
  npm --prefix "${UI_DIR}" ci
  npm --prefix "${UI_DIR}" run build
}

restart_services() {
  log "Restarting services..."
  sudo systemctl restart aris-backend.service aris-ui.service aris-kiosk.service
}

main() {
  require_tools
  update_repo
  rebuild_ui
  restart_services
  log "Update complete."
}

main "$@"
