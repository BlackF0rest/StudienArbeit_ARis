#!/usr/bin/env bash
set -euo pipefail

# Runtime configuration (can be overridden via environment).
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME:-/home/admin}/.Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

APP_URL="${ARIS_APP_URL:-http://127.0.0.1:4173}"
BACKEND_STATUS_URL="${ARIS_BACKEND_STATUS_URL:-http://127.0.0.1:5000/api/status}"
KIOSK_BROWSER="${ARIS_KIOSK_BROWSER:-midori}"
DISPLAY_ROTATION="${ARIS_DISPLAY_ROTATION:-inverted}"

is_low_ram_wrapper() {
  local candidate="$1"
  [[ -f "$candidate" ]] || return 1

  # Raspberry Pi wrapper scripts that show the "<1GB RAM" dialog are shell scripts.
  # Real chromium binaries are ELF and won't match this grep.
  head -n 200 "$candidate" 2>/dev/null | grep -q "less than 1GB of RAM"
}

find_chromium_binary() {
  local candidate=""
  local -a candidates=(
    "/usr/lib/chromium/chromium"
    "/usr/lib/chromium-browser/chromium-browser"
    "$(command -v chromium 2>/dev/null || true)"
    "$(command -v chromium-browser 2>/dev/null || true)"
    "$(command -v google-chrome 2>/dev/null || true)"
  )

  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" && -x "$candidate" ]] || continue
    if is_low_ram_wrapper "$candidate"; then
      echo "Skipping wrapper with low-RAM popup: $candidate"
      continue
    fi
    echo "$candidate"
    return 0
  done

  return 1
}

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

apply_display_rotation() {
  local rotation="$1"

  case "$rotation" in
    normal|left|right|inverted) ;;
    *)
      echo "Unsupported ARIS_DISPLAY_ROTATION value: $rotation (supported: normal, left, right, inverted)"
      return 1
      ;;
  esac

  if ! command -v xrandr >/dev/null 2>&1; then
    echo "xrandr is not installed; skipping display rotation"
    return 0
  fi

  local output=""
  output="$(xrandr --query | awk '/ connected/{print $1; exit}')"
  if [[ -z "$output" ]]; then
    echo "No connected display output found via xrandr; skipping rotation"
    return 0
  fi

  xrandr --output "$output" --rotate "$rotation"
}

# Wait for backend + UI server
for i in {1..60}; do
  curl -fsS "$BACKEND_STATUS_URL" >/dev/null 2>&1 && \
  curl -fsS "$APP_URL" >/dev/null 2>&1 && break
  echo "waiting for backend and UI server"
  sleep 1
done

# Hide cursor (optional)
unclutter -idle 0.1 -root &

apply_display_rotation "$DISPLAY_ROTATION"

case "$KIOSK_BROWSER" in
  cog)
    if ! command -v cog >/dev/null 2>&1; then
      echo "ARIS_KIOSK_BROWSER=cog requested, but cog is not installed"
      exit 1
    fi

    exec cog --platform=x11 "$APP_URL"
    ;;
  midori)
    BROWSER_BIN="$(find_midori_binary || true)"
    if [[ -z "$BROWSER_BIN" ]]; then
      echo "ARIS_KIOSK_BROWSER=midori requested, but no midori binary was found"
      exit 1
    fi

    exec "$BROWSER_BIN" -e Fullscreen -a "$APP_URL"
    ;;
  chromium)
    BROWSER_BIN="$(find_chromium_binary || true)"
    if [[ -z "$BROWSER_BIN" ]]; then
      echo "No usable chromium binary found (wrapper scripts were skipped)."
      exit 1
    fi
    ;;
  *)
    echo "Unsupported ARIS_KIOSK_BROWSER value: $KIOSK_BROWSER (supported: chromium, cog, midori)"
    exit 1
    ;;
esac

exec "$BROWSER_BIN" \
  --kiosk "$APP_URL" \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --no-first-run \
  --no-default-browser-check \
  --check-for-update-interval=31536000 \
  --autoplay-policy=no-user-gesture-required \
  --disable-features=TranslateUI \
  --disable-gpu \
  --use-gl=swiftshader \
  --disable-dev-shm-usage
