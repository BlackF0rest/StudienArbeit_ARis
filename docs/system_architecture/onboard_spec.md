# Onboard System Architecture Specification

## 1) Final Module Map

The onboard platform is organized into the following modules and boundaries:

```text
+-------------------------+             +----------------------------+
|       PC Interface      | <---------> | Python Backend             |
| (Desktop tools / debug) |             | (orchestrator + API host)  |
+-------------------------+             +-------------+--------------+
                                                      |
                                                      | REST/WebSocket/RPC
                                                      v
+-------------------------+             +-------------+--------------+
| Web UI Frontend         | <---------> | App-Interface Layer         |
| (device UI client)      |             | (capability registry,       |
+-------------------------+             | routing, lifecycle)         |
                                        +------+------+---------------+
                                               |      |
                           App commands/events |      | Radio/USB tunnel
                                               v      v
                                        +------+------+---------------+
                                        | Feature Apps                |
                                        | (Teleprompter, Navigation, |
                                        | HUD, etc.)                  |
                                        +------+------+---------------+
                                               |
                                               | Runtime APIs
                                               v
+-------------------------+             +------+------+---------------+
| HID Devices             | ----------- | Feature Runtime             |
| (buttons/touch/etc.)    | events      | (execution + state machine) |
+-------------------------+             +------+------+---------------+
                                               ^
+-------------------------+             +------+-----------------------+
| Sensors                 | ----------- | Sensor/HID adapters         |
| (IMU/GNSS/etc.)         | streams     +-----------------------------+
+-------------------------+

+-------------------------+
| Display Driver          |
| (frame composition +    |
| panel refresh control)  |
+-------------------------+

+-------------------------+
| SQL Database            |
| (persistent config,     |
| sessions, logs)         |
+-------------------------+

+-------------------------+
| Debugging-Interface     |
| (trace, health, metrics)|
+-------------------------+
```

### Module responsibilities

- **Display driver:** final rendering path to the panel; applies frame timing and composition primitives.
- **Web UI frontend:** user-facing controls and views.
- **Python backend:** central coordination, policy decisions, API serving, persistence orchestration.
- **SQL DB:** durable storage for configuration, sessions, and audit/log metadata.
- **Feature apps:** user-facing app logic (teleprompter, navigation, HUD overlays).
- **App-interface:** stable capability boundary for feature-app registration and invocation.
- **Debugging-interface:** diagnostics endpoint for logs, traces, metrics, and fault snapshots.
- **HID:** local human-input events (buttons, gesture pads, rotary encoders, etc.).
- **Sensors:** telemetry providers (IMU, location, environmental, optional external streams).
- **PC interface:** tethered host integration for development, syncing, and external control.

---

## 2) Interface Contracts (one per boundary)

### A. Frontend ↔ Backend

**Protocol:** HTTPS REST + WebSocket.

**Contract:**
- Frontend sends authenticated REST commands (`/api/v1/*`) for mutations.
- Backend returns typed JSON (`status`, `data`, `error`) with monotonic `server_time_ms`.
- Frontend subscribes to WebSocket topics (`hud.state`, `teleprompter.state`, `nav.state`, `health`) for push updates.
- Schema version is carried in headers (`X-Api-Version`) and payload root (`schema_version`).

**Compatibility rule:** backend supports the current and previous minor frontend schema version.

### B. Backend ↔ App-Interface

**Protocol:** in-process Python contract (typed DTOs + async callbacks).

**Contract:**
- Backend invokes `register_app(manifest)`, `start(context)`, `stop(reason)`, `handle_command(command)`.
- App-interface emits `StateDelta`, `Event`, `HealthSignal` back to backend.
- All app commands are idempotency-keyed to prevent duplicate side effects.

**Compatibility rule:** app manifests are versioned (`app_api_semver`); breaking changes require explicit adapter.

### C. App-Interface ↔ Bluetooth/USB/WiFi

**Protocol:** transport-agnostic framed messages.

**Contract:**
- Envelope: `{msg_id, correlation_id, capability, op, payload, timestamp_ms, qos}`.
- Supported QoS classes:
  - `qos=0`: best-effort, no retransmit (non-critical telemetry).
  - `qos=1`: at-least-once with ACK + retry (control commands).
- MTU-aware chunking for Bluetooth and reassembly in app-interface.
- Transport abstraction must expose `connect()`, `disconnect()`, `send(frame)`, `on_frame(callback)`, `health()`.

**Compatibility rule:** capability namespace is stable; unknown capability/op must return structured `UNSUPPORTED` error.

### D. HID/Sensors ↔ Feature-Runtime

**Protocol:** event bus with typed messages.

**Contract:**
- HID emits discrete events (`PRESS`, `RELEASE`, `LONG_PRESS`, `GESTURE`) with source and timestamp.
- Sensors emit sampled records with sequence number and confidence.
- Feature-runtime consumes via subscriptions with explicit backpressure policy (`drop_oldest` default).
- Event ordering is guaranteed per source stream.

**Compatibility rule:** sensor schema version is pinned per stream; runtime rejects mismatched major versions.

---

## 3) Data Ownership Rules

### Volatile state (in-memory, non-durable)

Store in volatile state:
- Active HUD frame model and transient render caches.
- Live teleprompter cursor position, playback speed changes not yet committed.
- Current navigation route progress and short-lived sensor fusion buffers.
- Transport session handles, connection health counters, and retry windows.

### SQL database (durable)

Store in SQL DB:
- User/system configuration (UI preferences, device calibration, feature toggles).
- Saved teleprompter scripts and reading profiles.
- Navigation favorites/history, persistent waypoints, map source preferences.
- Session summaries, fault history, and operational audit records.

### Source-of-truth assignment

- **Teleprompter:**
  - Script content + profile defaults: **SQL DB is source of truth**.
  - Moment-to-moment reading position during a running session: **feature runtime is source of truth** (checkpointed periodically to DB).
- **Navigation:**
  - Persisted routes/favorites/preferences: **SQL DB is source of truth**.
  - Active route progression and ETA adjustments: **backend + feature runtime are runtime source of truth**.
- **HUD state:**
  - Live composited HUD model: **feature runtime is source of truth**.
  - Last known stable HUD configuration template: **SQL DB is source of truth**.

---

## 4) Latency and Update-Rate Targets

Target operational budgets (normal mode):

- **HUD refresh:** 60 Hz target (16.7 ms frame budget), acceptable degraded mode at 30 Hz.
- **Teleprompter update interval:** 20-50 ms command-to-visual reaction; cursor/state broadcast every 100 ms.
- **Sensor event frequency:**
  - IMU-class high-rate stream: 100 Hz nominal.
  - GNSS/location-class stream: 1-10 Hz depending on source.
  - HID button/gesture events: interrupt-driven, end-to-end handling < 30 ms target.
- **Frontend state push cadence:** 10 Hz for interactive state channels, burstable for critical events.
- **Backend command acknowledgement:** < 100 ms p95 on local links; < 250 ms p95 on wireless links.

---

## 5) Error-Handling Policy per Interface

### Frontend ↔ Backend

- **Timeout:** REST default 2 s; retryable endpoints up to 2 retries with exponential backoff (200 ms, 800 ms).
- **Retry policy:** only idempotent operations auto-retried by client.
- **Degraded mode:** if WebSocket drops, frontend falls back to polling every 1 s and marks UI as "limited live updates".

### Backend ↔ App-Interface

- **Timeout:** app command execution soft timeout 500 ms, hard timeout 2 s.
- **Retry policy:** backend retries once for transient app unavailability; no blind retry on non-idempotent commands.
- **Degraded mode:** backend isolates failing app, keeps core services alive, and surfaces health event via debugging-interface.

### App-Interface ↔ Bluetooth/USB/WiFi

- **Timeout:** ACK timeout transport-specific (Bluetooth 300 ms, USB 100 ms, WiFi 250 ms baseline).
- **Retry policy:** QoS1 retries up to 3 times with jittered backoff; QoS0 no retry.
- **Degraded mode:** on repeated link loss, demote to reduced-bandwidth profile and pause non-critical streams.

### HID/Sensors ↔ Feature-Runtime

- **Timeout:** stale sensor threshold at 3× expected sample period.
- **Retry policy:** adapter attempts device re-init for recoverable sensor faults; HID reconnect loop with capped backoff.
- **Degraded mode:** runtime continues with last-good sensor state plus confidence decay; disables affected features if confidence drops below safe threshold.

### Cross-cutting diagnostics

- Every boundary emits structured errors: `{code, message, component, correlation_id, recoverable}`.
- Debugging-interface must expose rolling error counters and last-fault snapshots for each module.
