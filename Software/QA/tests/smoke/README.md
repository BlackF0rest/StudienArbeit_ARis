# Smoke Test Suite

This directory is reserved for ultra-fast smoke test entry points.
Current smoke scenarios are implemented in `../integration/test_smoke_scenarios.py` and executed via `make qa-smoke`.
They include API smoke paths plus HID gesture normalization checks for canonical `single`/`double` semantics.
