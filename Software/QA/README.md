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
