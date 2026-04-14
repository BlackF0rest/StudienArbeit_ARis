# ARis Repository

## Current Architecture

The repository is now organized around active product tracks under `Software/`:

- `Software/Backend` — active backend services and APIs.
- `Software/Onboard_UI` — active onboard UI track.
- `Software/Onboard_Runtime` — active onboard runtime and hardware integration.
- `Software/QA` — quality assurance tests, scripts, and reports.
- `Software/Companion_Prototype/ReactNative_Companion` — active mobile companion track.

See `docs/repo_map.md` for owners and purpose details.

Launch-approved onboard routes are documented in `docs/release/onboard_route_manifest.md` (`/`, `/Navigation`, `/Teleprompter`, `/Messages`).
Development/operator routes (`/Debug`, `/dev/*`) are outside launch scope.

Compatibility notice (one release cycle): legacy paths `Software/Backend_Prototype` and `Software/Svelte_Testing/minimal_hud` remain as symlinks to the new locations.

## Team safety rules (Pi + local development)

- Never run `sudo pip` inside a project virtual environment (`.venv`).
- Never run `sudo npm` in project directories.
- If a repository tree becomes root-owned after accidental `sudo`, restore ownership before reinstalling dependencies (example: `sudo chown -R pi:pi /home/pi/aris`).

## Legacy Archived

The following legacy prototypes were archived (not hard-deleted) to:

- `archive/legacy_prototypes/2026-04-06/Software/Companion_Prototype/Vue_Companion_App`
- `archive/legacy_prototypes/2026-04-06/Software/Testing/Django_Testing`
- `archive/legacy_prototypes/2026-04-06/Software/Testing/ESP8266_Testing`
- `archive/legacy_prototypes/2026-04-06/Software/Testing/T-Beam_Micropython_Testing`

Planned lifecycle:
1. Keep archived assets for one successful release cycle.
2. Permanently delete archived legacy paths after that release cycle.
