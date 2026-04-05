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
4. **Configuration loader**
   - file-based JSON config
   - environment overrides via `ARIS_RUNTIME_` prefix
5. **Startup profiles**
   - `dev`: verbose (`DEBUG`) logging
   - `demo`: stable defaults enabled
   - `headless`: UI disabled for diagnostics

## Quick Start

```python
from Software.Onboard_Runtime import OnboardRuntime

runtime = OnboardRuntime.from_config("Software/Onboard_Runtime/config.example.json")
config = runtime.load_config()
runtime.register_core_modules()
runtime.start_all()
```
