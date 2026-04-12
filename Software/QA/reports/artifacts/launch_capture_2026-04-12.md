# Launch route capture run (600x400)

Date: 2026-04-12 (UTC)
Routes requested: `/`, `/Navigation`, `/Teleprompter`, `/Messages`
Target profile: `600x400`

## Capture command attempts

1. `cd Software/Onboard_UI && npm ci`  
   - Result: dependencies installed.
2. `cd Software/Onboard_UI && npx playwright install chromium`  
   - Result: failed (`403 Forbidden` from npm registry).
3. Browser binary discovery (`which chromium-browser || which chromium || which google-chrome || which firefox`)  
   - Result: no browser present in environment.

## Outcome

Automated screenshots/video could not be produced in this environment because no browser runtime is available and browser tooling download is blocked by network policy.

When environment access is restored, rerun with a browser-enabled worker and generate:
- `route-home-600x400.png`
- `route-navigation-600x400.png`
- `route-teleprompter-600x400.png`
- `route-messages-600x400.png`
- `launch-routes-600x400.mp4`
