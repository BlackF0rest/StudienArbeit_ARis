# Global Input Interaction Contract

This contract defines one normalized HID interaction model for the onboard HUD.

## Core gestures

- **Short press**: **next item / next app / speed up** (context aware).
- **Long press**: **enter/select OR pause/resume OR back/home** (context aware).

## Explicit exclusion

- **AI chat text input is excluded from this contract**.
- Chat compose input is handled via companion app input (phone/secondary device), not onboard HID short/long press.

## FSM model

The frontend input controller consumes backend/runtime normalized events (`input.control`) and tracks a minimal finite-state machine:

1. **Home carousel**
2. **Feature active**
3. **Confirm/exit state**

## Per-feature routing behavior

- **Home**: short = next app, long = open selected app.
- **Teleprompter**: short = speed + step, long = pause/resume.
- **Navigation**: short = cycle info panel, long = return home.
- **Messages/HUD**: short = cycle sections, long = return home.

## Usability hint

Each page must display a one-line helper overlay:

`short: … | long: …`
