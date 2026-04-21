# Global Input Interaction Contract

This contract defines one normalized HID interaction model for the onboard HUD.

## Core gestures

- **Single tap**: **next item / next app / speed up** (context aware).
- **Double tap**: **enter/select OR pause/resume OR back/home** (context aware).

## Latched switch state (runtime contract extension)

Each `input.control` payload carries two semantic layers:

1. `gesture`: transient interaction (`single` or `double`)
2. `switch_state`: stable latched state (`high` or `low`)

Behavior:

- **Single tap toggles** `switch_state` between `high` and `low`.
- **Double tap preserves** the currently latched `switch_state` (no toggle side-effect).
- This keeps navigation double-tap behavior intact while exposing a robust on/off-style control bit.

## Explicit exclusion

- **AI chat text input is excluded from this contract**.
- Chat compose input is handled via companion app input (phone/secondary device), not onboard HID single/double tap.

## FSM model

The frontend input controller consumes backend/runtime normalized events (`input.control`) and tracks a minimal finite-state machine:

1. **Home carousel**
2. **Feature active**
3. **Confirm/exit state**

## Per-feature routing behavior

- **Home**: single = next app, double = open selected app.
- **Teleprompter**: single = speed + step, double = pause/resume.
- **Navigation**: single = cycle info panel, double = return home.
- **Messages/HUD**: single = cycle sections, double = return home.

## Usability hint

Each page must display a one-line helper overlay:

`single: … | double: …`

## Canonical payload shape (`event_type = "input.control"`)

```json
{
  "event_type": "input.control",
  "source": "hid:<button-id>",
  "value": {
    "gesture": "single",
    "switch_state": "high",
    "tap_count": 1,
    "duration_ms": 83,
    "source": "hid:<button-id>"
  },
  "unit": null,
  "timestamp": "2026-04-21T00:00:00+00:00"
}
```
