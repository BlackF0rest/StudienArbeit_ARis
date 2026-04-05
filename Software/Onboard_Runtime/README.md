# Onboard Runtime

`Software/Onboard_Runtime/` consolidates shared runtime concerns for onboard software modules.

## Included Components

1. **Module lifecycle manager**
   - Methods: `init`, `start`, `stop`, `health`, `get_version`
2. **Central module registry** with categories for:
   - backend service
   - feature app host
   - hardware adapters
   - communication adapters
3. **Shared event bus** for cross-module events:
   - button press
   - sensor update
   - teleprompter update
   - connection status
   - normalized hardware event
4. **Hardware service modules**
   - HID input adapter with debouncing + short/long press semantics
   - sensor interfaces/adapters for BME280 + gyro (extensible via `SensorAdapter`)
   - `HardwareEvent` schema (`event_type`, `source`, `value`, `unit`, `timestamp`)
   - `HardwareEventPublisher` for publishing hardware events to runtime bus
   - feature subscriptions for Basic HUD, Navigation, and Teleprompter
5. **Configuration loader**
   - file-based JSON config
   - environment overrides via `ARIS_RUNTIME_` prefix
6. **Startup profiles**
   - `dev`: verbose (`DEBUG`) logging
   - `demo`: stable defaults enabled
   - `headless`: UI disabled for diagnostics

## Quick Start

```python
from Software.Onboard_Runtime import OnboardRuntime

runtime = OnboardRuntime.from_config("Software/Onboard_Runtime/config.example.json")
config = runtime.load_config()
runtime.register_core_modules()
subscriptions = runtime.register_feature_subscriptions()
runtime.start_all()
```
