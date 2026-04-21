# Global Input Interaction Contract

This contract defines one normalized HID interaction model for the onboard HUD.

## Core gestures

- **Single tap**: **next item / next app / speed up** (context aware).
- **Double tap**: **enter/select OR pause/resume OR back/home** (context aware).

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
