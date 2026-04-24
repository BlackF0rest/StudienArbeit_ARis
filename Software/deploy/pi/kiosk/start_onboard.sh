#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME:-/home/admin}/.Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

BACKEND_URL="${ARIS_BACKEND_URL:-http://127.0.0.1:5000}"
FRONTEND_URL="${ARIS_FRONTEND_URL:-http://127.0.0.1:4173}"

find_midori_binary() {
  local candidate=""
  local -a candidates=(
    "$(command -v midori 2>/dev/null || true)"
    "$(command -v midori-browser 2>/dev/null || true)"
  )

  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" && -x "$candidate" ]] || continue
    echo "$candidate"
    return 0
  done

  return 1
}

for i in {1..60}; do
  if curl -fsS "$BACKEND_URL" >/dev/null 2>&1 && curl -fsS "$FRONTEND_URL" >/dev/null 2>&1; then
    break
  fi
  echo "Warte auf Backend ($BACKEND_URL) und Frontend ($FRONTEND_URL)"
  sleep 1
done

if command -v flatpak >/dev/null 2>&1 && flatpak info org.midori_browser.Midori >/dev/null 2>&1; then
  exec flatpak run org.midori_browser.Midori "$FRONTEND_URL"
fi

BROWSER_BIN="$(find_midori_binary || true)"
if [[ -z "$BROWSER_BIN" ]]; then
  echo "Midori wurde nicht gefunden (weder Flatpak noch native Binary)."
  exit 1
fi

exec "$BROWSER_BIN" -e Fullscreen -a "$FRONTEND_URL"
