from __future__ import annotations

from datetime import datetime, timedelta, timezone

from Software.QA.scripts.backend_test_harness import (
    BackendServer,
    TestResult,
    assert_true,
    request_json,
)
from Software.Onboard_Runtime.event_bus import RuntimeEvent, SharedEventBus
from Software.Onboard_Runtime.hardware import HIDInputAdapter, HIDRuntimeEventPump, HardwareEventPublisher
from Software.Onboard_Runtime.hardware.subscriptions import _normalize_input_control_value


def run_smoke_scenarios() -> list[TestResult]:
    results: list[TestResult] = []

    with BackendServer() as server:
        try:
            scenario_payload = {
                "text": "Scenario A payload",
                "speed": 55,
                "fontSize": 3,
                "fontColor": "#ff0",
                "backgroundColor": "#111",
                "fontFamily": "Courier New",
                "lineHeight": 1.4,
                "opacity": 0.8,
            }
            send = request_json(server.base_url, "POST", "/api/teleprompter/send", payload=scenario_payload)
            assert_true(send["status"] == 200, "Scenario A send should return 200")

            current = request_json(server.base_url, "GET", "/api/teleprompter/current")
            assert_true(current["status"] == 200, "Scenario A current should return 200")
            current_data = current["json"]["data"]
            assert_true(current_data == scenario_payload, "Scenario A expected current config to match posted payload")
            results.append(TestResult(name="scenario_a_send_then_current", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="scenario_a_send_then_current", passed=False, reason=str(exc)))

        try:
            reset = request_json(server.base_url, "POST", "/api/teleprompter/reset")
            assert_true(reset["status"] == 200, "Scenario B reset should return 200")
            reset_config = reset["json"]["data"]["config"]
            assert_true(reset_config["speed"] == 30, "Scenario B reset should restore default speed")
            assert_true(
                reset_config["text"].startswith("Willkommen zur AR-Brille"),
                "Scenario B reset should restore default text",
            )
            results.append(TestResult(name="scenario_b_reset_defaults", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="scenario_b_reset_defaults", passed=False, reason=str(exc)))

        try:
            request_json(server.base_url, "DELETE", "/api/messages")
            create = request_json(server.base_url, "POST", "/api/messages", payload={"content": "Scenario C"})
            assert_true(create["status"] == 200, "Scenario C create should return 200")

            listed = request_json(server.base_url, "GET", "/api/messages")
            assert_true(listed["status"] == 200, "Scenario C list should return 200")
            assert_true(
                any(item.get("content") == "Scenario C" for item in listed["json"]["data"]),
                "Scenario C message was not found in list",
            )

            deleted = request_json(server.base_url, "DELETE", "/api/messages")
            assert_true(deleted["status"] == 200, "Scenario C delete should return 200")
            listed_after = request_json(server.base_url, "GET", "/api/messages")
            assert_true(len(listed_after["json"]["data"]) == 0, "Scenario C should leave no messages")
            results.append(TestResult(name="scenario_c_messages_roundtrip", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="scenario_c_messages_roundtrip", passed=False, reason=str(exc)))

    try:
        short_press = _normalize_input_control_value({"press": "short_press"})
        assert_true(short_press["gesture"] == "single", "Legacy short_press should normalize to single")

        long_press = _normalize_input_control_value({"press": "long_press"})
        assert_true(long_press["gesture"] == "double", "Legacy long_press should normalize to double")

        canonical_single = _normalize_input_control_value({"gesture": "single"})
        assert_true(canonical_single["gesture"] == "single", "Canonical single gesture should remain unchanged")

        canonical_double = _normalize_input_control_value({"gesture": "double"})
        assert_true(canonical_double["gesture"] == "double", "Canonical double gesture should remain unchanged")
        results.append(TestResult(name="scenario_d_hid_gesture_normalization", passed=True))
    except Exception as exc:  # noqa: BLE001
        results.append(TestResult(name="scenario_d_hid_gesture_normalization", passed=False, reason=str(exc)))

    try:
        event_bus = SharedEventBus()
        publisher = HardwareEventPublisher(event_bus)
        adapter = HIDInputAdapter(double_tap_window_ms=350)
        event_pump = HIDRuntimeEventPump(adapter=adapter, publisher=publisher)
        emitted_events: list[dict[str, object]] = []

        event_bus.subscribe(RuntimeEvent.HARDWARE_EVENT, lambda message: emitted_events.append(message.payload))

        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        event_pump.process_transition(button_id="button-a", pressed=True, at=t0)
        event_pump.process_transition(button_id="button-a", pressed=False, at=t0 + timedelta(milliseconds=60))
        assert_true(len(emitted_events) == 0, "Single tap should remain pending before timeout flush")

        event_pump.tick(at=t0 + timedelta(milliseconds=500))
        assert_true(len(emitted_events) == 1, "Timeout flush should emit exactly one event")

        first_event = emitted_events[0]
        event_value = first_event.get("value") if isinstance(first_event, dict) else None
        assert_true(isinstance(event_value, dict), "Emitted hardware payload must contain value object")
        assert_true(event_value.get("gesture") == "single", "Flush should emit gesture=single")
        results.append(TestResult(name="scenario_e_single_tap_timeout_flush", passed=True))
    except Exception as exc:  # noqa: BLE001
        results.append(TestResult(name="scenario_e_single_tap_timeout_flush", passed=False, reason=str(exc)))

    return results


if __name__ == "__main__":
    failures = [result for result in run_smoke_scenarios() if not result.passed]
    if failures:
        for failure in failures:
            print(f"FAIL {failure.name}: {failure.reason}")
        raise SystemExit(1)
    print("PASS all smoke scenarios")
