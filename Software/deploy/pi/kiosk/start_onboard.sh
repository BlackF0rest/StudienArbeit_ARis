#!/usr/bin/env bash
set -euo pipefail

export DISPLAY=:0
export XAUTHORITY=/home/admin/.Xauthority
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"

# Wait for backend + UI server
for i in {1..60}; do
  curl -fsS http://127.0.0.1:5000/api/status >/dev/null 2>&1 && \
  curl -fsS http://127.0.0.1:4173 >/dev/null 2>&1 && break
  echo "whaiting for backend and UI Server"
  sleep 1
done

# Hide cursor (optional)
unclutter -idle 0.1 -root &

# Kiosk Chromium
chromium-browser \
  --kiosk http://127.0.0.1:4173 \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  --autoplay-policy=no-user-gesture-required \
  --disable-features=TranslateUI
