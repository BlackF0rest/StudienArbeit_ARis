#!/usr/bin/env bash
set -euo pipefail

# =========================
# ARis Kiosk Startup Script
# =========================

# --- Config (anpassbar) ---
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:5000/api/status}"
UI_URL="${UI_URL:-http://127.0.0.1:4173}"
KIOSK_URL="${KIOSK_URL:-http://127.0.0.1:4173}"

# Rotation: normal | left | right | inverted
ROTATION="${ROTATION:-inverted}"

# UI scaling in Chromium (1.0 = normal, 1.4..2.0 = größer)
UI_SCALE="${UI_SCALE:-1.6}"

# AR panel target size
WINDOW_WIDTH="${WINDOW_WIDTH:-600}"
WINDOW_HEIGHT="${WINDOW_HEIGHT:-400}"

# User/home (an dein Setup angepasst)
export HOME="${HOME:-/home/admin}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/admin/.Xauthority}"

log() {
  printf '[start_onboard] %s\n' "$1"
}

# --- Wait for services ---
log "Waiting for backend and UI server..."
for i in {1..120}; do
  if curl -fsS "$BACKEND_URL" >/dev/null 2>&1 && curl -fsS "$UI_URL" >/dev/null 2>&1; then
    log "Backend and UI are reachable."
    break
  fi
  sleep 1
done

# --- Display housekeeping ---
xset s off || true
xset -dpms || true
xset s noblank || true
unclutter -idle 0.1 -root || true

# Rotate active output (if any)
OUTPUT_NAME="$(xrandr --query 2>/dev/null | awk '/ connected/{print $1; exit}')"
if [[ -n "${OUTPUT_NAME}" ]]; then
  log "Detected output: ${OUTPUT_NAME} (rotation: ${ROTATION})"
  xrandr --output "${OUTPUT_NAME}" --rotate "${ROTATION}" || true
else
  log "No connected xrandr output detected; skipping rotation."
fi

# --- Browser detection ---
BROWSER_BIN="$(command -v chromium-browser || command -v chromium || true)"
if [[ -z "${BROWSER_BIN}" ]]; then
  log "ERROR: chromium-browser/chromium not found in PATH."
  sleep 10
  exit 1
fi

log "Launching Chromium kiosk: ${KIOSK_URL}"

# --- Chromium kiosk ---
exec "${BROWSER_BIN}" \
  --kiosk "${KIOSK_URL}" \
  --user-data-dir="${HOME}/.config/chromium-kiosk" \
  --no-first-run \
  --no-default-browser-check \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --incognito \
  --autoplay-policy=no-user-gesture-required \
  --disable-features=TranslateUI \
  --force-device-scale-factor="${UI_SCALE}" \
  --high-dpi-support=1 \
  --window-size="${WINDOW_WIDTH},${WINDOW_HEIGHT}" \
  --disable-gpu \
  --use-gl=swiftshader \
  --noerrdialogs
