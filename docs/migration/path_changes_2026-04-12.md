# Path Migration: 2026-04-12

This document records repository path changes introduced on **2026-04-12**.

## Directory renames

| Old path | New path |
|---|---|
| `Software/Backend_Prototype` | `Software/Backend` |
| `Software/Svelte_Testing/minimal_hud` | `Software/Onboard_UI` |

## Temporary compatibility (one release cycle)

To preserve compatibility for existing scripts and local setups, the legacy paths are currently provided as symlinks:

- `Software/Backend_Prototype` -> `Software/Backend`
- `Software/Svelte_Testing/minimal_hud` -> `Software/Onboard_UI`

After one successful release cycle, these compatibility symlinks should be removed.
