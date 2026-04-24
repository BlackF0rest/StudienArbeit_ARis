#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SYSTEMD_SOURCE_DIR="${SCRIPT_DIR}/systemd"
SYSTEMD_TARGET_DIR="/etc/systemd/system"

log() {
  printf '[install_pi] %s\n' "$1"
}

require_sudo() {
  if [[ "${EUID}" -ne 0 ]]; then
    log "Please run as root (e.g. sudo bash Software/deploy/pi/install_pi.sh)."
    exit 1
  fi
}

install_apt_dependencies() {
  log "Installing apt dependencies..."
  apt-get update
  apt-get install -y \
    python3 python3-pip python3-venv sqlite3 \
    xserver-xorg xinit openbox chromium-browser unclutter curl git \
    ca-certificates fonts-dejavu flatpak

  if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    log "Installing Node.js 20 from NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
  else
    log "Node.js already installed: $(node -v), npm: $(npm -v)"
  fi
}

install_midori_optional() {
  local apt_log
  apt_log="$(mktemp)"

  log "Attempting optional Midori install via apt..."
  if apt-get install -y midori >"${apt_log}" 2>&1; then
    log "Optional Midori apt install succeeded."
  else
    if grep -q "Unable to locate package midori" "${apt_log}"; then
      log "WARNING: Optional package 'midori' not available via apt on this distro. Continuing without native Midori."
    else
      log "WARNING: Optional Midori apt install failed. Continuing. See details below:"
      sed 's/^/[install_pi] /' "${apt_log}" || true
    fi
  fi

  rm -f "${apt_log}"
}

warn_if_no_midori_path() {
  local has_native_midori=0
  local has_flatpak_midori=0

  if command -v midori >/dev/null 2>&1 || command -v midori-browser >/dev/null 2>&1; then
    has_native_midori=1
  fi

  if command -v flatpak >/dev/null 2>&1 && flatpak info org.midori_browser.Midori >/dev/null 2>&1; then
    has_flatpak_midori=1
  fi

  if [[ "${has_native_midori}" -eq 0 && "${has_flatpak_midori}" -eq 0 ]]; then
    log "WARNING: No Midori runtime detected (neither apt binary nor Flatpak app org.midori_browser.Midori)."
    log "WARNING: Node/Python build and systemd setup completed, but kiosk browser startup will fail until Midori is installed."
  fi
}

install_node_dependencies() {
  local ui_dir="${REPO_ROOT}/Software/Onboard_UI"

  log "Installing Node dependencies in ${ui_dir}..."
  npm --prefix "${ui_dir}" ci
  npm --prefix "${ui_dir}" run build
}

install_python_dependencies() {
  local backend_dir="${REPO_ROOT}/Software/Backend"
  local venv_dir="${backend_dir}/.venv"

  log "Setting up Python virtualenv in ${backend_dir}..."
  if [[ ! -d "${venv_dir}" ]]; then
    python3 -m venv "${venv_dir}"
  fi

  "${venv_dir}/bin/pip" install --upgrade pip
  "${venv_dir}/bin/pip" install flask flask-cors RPi.GPIO smbus2
}

copy_systemd_service_if_needed() {
  local source_file="$1"
  local target_file="${SYSTEMD_TARGET_DIR}/$(basename "${source_file}")"

  if [[ -f "${target_file}" ]] && cmp -s "${source_file}" "${target_file}"; then
    log "Service unchanged: $(basename "${source_file}")"
    return 1
  fi

  install -m 0644 "${source_file}" "${target_file}"
  log "Installed/updated service: $(basename "${source_file}")"
  return 0
}

install_systemd_services() {
  log "Installing systemd service files..."
  local changed=0

  copy_systemd_service_if_needed "${SYSTEMD_SOURCE_DIR}/aris-backend.service" && changed=1 || true
  copy_systemd_service_if_needed "${SYSTEMD_SOURCE_DIR}/aris-ui.service" && changed=1 || true
  copy_systemd_service_if_needed "${SYSTEMD_SOURCE_DIR}/aris-kiosk.service" && changed=1 || true

  if [[ "${changed}" -eq 1 ]]; then
    log "Reloading systemd daemon..."
    systemctl daemon-reload
  else
    log "No service file changes detected; skipping daemon-reload."
  fi

  log "Enabling and starting services..."
  systemctl enable --now aris-backend.service aris-ui.service aris-kiosk.service
}

main() {
  require_sudo
  install_apt_dependencies
  install_midori_optional
  install_node_dependencies
  install_python_dependencies
  install_systemd_services
  warn_if_no_midori_path
  log "Installation complete."
}

main "$@"
