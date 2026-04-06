# 600x400 HUD Target Profile

This profile constrains the HUD for low-resolution optical displays (600x400).

## Layout constraints

1. Maximum **3 major blocks** visible at once on Host/Home.
2. Default content density is capped to **2 text lines per block** (`.hud-compact-line`).
3. Full telemetry and diagnostics are **not shown on Home**.

## Screen intent

- **Home/Host**: selected app + connection summary + current input hint.
- **Debug**: detailed telemetry and PC link diagnostics.
- **Navigation**: one active panel at a time with enlarged key text and heading marker.
- **Messages**: compact status and latest 1-2 messages by default.
- **Teleprompter**: full-screen script remains primary; overlays are minimized.
