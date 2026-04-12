# QA Automation Policy

## Easy-first rollout

The first automation PR must fully cover all API and software-only integration acceptance criteria.
Hardware-coupled criteria remain `manual` until a hardware-in-loop runner exists.

Hardware-coupled examples currently classified as manual:

- Sensor pin validation on target hardware.
- Physical HID interactions.
- BLE checks on the target adapter.
- Extended soak/runtime stability checks.

## Baseline trend tracking

CI keeps a bounded history of acceptance reports in `Software/QA/reports/history` and compares each run with the previous baseline.
The gate fails when P0 pass-rate regresses versus the prior run.

## Companion readiness policy (hard gate)

For any **"ready for companion"** decision, the following evidence is mandatory:

- `Software/QA/reports/latest.json` (or CI artifact link).
- `Software/QA/reports/latest.md` (or CI artifact link).

Manual criteria `MAN-001..MAN-004` must be tracked explicitly with:

- disposition (`PASS`, `FAIL`, `WAIVED`, `BLOCKED`, or `UNSET`),
- owner,
- date,
- optional notes.

Hard policy for starting a companion sprint:

1. All automatable `P0` checks pass.
2. `P0` pass-rate did not regress versus baseline.
3. Manual `P1` checks have a clear disposition (`PASS`, `FAIL`, `WAIVED`, or `BLOCKED`).

If any requirement above is not met, companion sprint start is **not allowed**.
