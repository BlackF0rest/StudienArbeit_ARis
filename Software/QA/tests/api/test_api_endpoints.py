from __future__ import annotations

from typing import Any

from Software.QA.scripts.backend_test_harness import (
    BackendServer,
    TestResult,
    assert_true,
    request_json,
)

EXPECTED_TP_KEYS = {
    "text",
    "speed",
    "fontSize",
    "fontColor",
    "backgroundColor",
    "fontFamily",
    "lineHeight",
    "opacity",
}


def _unwrap_ok_payload(response: dict[str, Any]) -> dict[str, Any]:
    assert_true(response["status"] == 200, f"Expected HTTP 200, got {response['status']}")
    payload = response["json"]
    assert_true(payload.get("ok") is True, "Expected response with ok=true")
    assert_true("data" in payload, "Expected response to contain data")
    return payload["data"]


def run_api_tests() -> list[TestResult]:
    results: list[TestResult] = []

    with BackendServer() as server:
        auth_headers = {}
        try:
            server.bootstrap_auth()
            auth_headers = server.default_headers
            results.append(TestResult(name="auth_pairing_bootstrap", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="auth_pairing_bootstrap", passed=False, reason=str(exc)))

        try:
            status_response = request_json(server.base_url, "GET", "/api/status")
            status_data = _unwrap_ok_payload(status_response)
            assert_true("health" in status_data, "Status payload missing health field")
            results.append(TestResult(name="status_endpoint", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="status_endpoint", passed=False, reason=str(exc)))


        try:
            sensors_response = request_json(server.base_url, "GET", "/api/sensors", default_headers=auth_headers)
            sensors_data = _unwrap_ok_payload(sensors_response)
            assert_true("button" in sensors_data, "Sensors payload missing button field")
            assert_true("mpu6050" in sensors_data, "Sensors payload missing mpu6050 field")
            assert_true("gy63" in sensors_data, "Sensors payload missing gy63 field")
            results.append(TestResult(name="sensors_snapshot", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="sensors_snapshot", passed=False, reason=str(exc)))


        try:
            navigation_response = request_json(
                server.base_url,
                "GET",
                "/api/navigation/current",
                default_headers=auth_headers,
            )
            navigation = _unwrap_ok_payload(navigation_response)
            assert_true("heading" in navigation, "Navigation payload missing heading")
            assert_true("orientation" in navigation, "Navigation payload missing orientation")
            assert_true("timestamp" in navigation, "Navigation payload missing timestamp")
            assert_true("source" in navigation, "Navigation payload missing source")
            results.append(TestResult(name="navigation_current_snapshot", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="navigation_current_snapshot", passed=False, reason=str(exc)))

        try:
            diagnostics_response = request_json(server.base_url, "GET", "/api/debug/diagnostics")
            assert_true(
                diagnostics_response["status"] == 200,
                f"Expected HTTP 200, got {diagnostics_response['status']}",
            )
            panels = diagnostics_response["json"].get("panels", {})
            assert_true("pc_link" in panels, "Diagnostics payload missing panels.pc_link")
            results.append(TestResult(name="debug_diagnostics_endpoint", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="debug_diagnostics_endpoint", passed=False, reason=str(exc)))

        try:
            unknown_route_response = request_json(server.base_url, "GET", "/api/does-not-exist")
            assert_true(
                unknown_route_response["status"] == 404,
                f"Expected HTTP 404, got {unknown_route_response['status']}",
            )
            results.append(TestResult(name="unknown_route_404", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="unknown_route_404", passed=False, reason=str(exc)))

        try:
            delete_response = request_json(server.base_url, "DELETE", "/api/messages", default_headers=auth_headers)
            _unwrap_ok_payload(delete_response)

            post_response = request_json(
                server.base_url,
                "POST",
                "/api/messages",
                payload={"content": "qa-message"},
                default_headers=auth_headers,
            )
            _unwrap_ok_payload(post_response)

            get_response = request_json(server.base_url, "GET", "/api/messages", default_headers=auth_headers)
            messages = _unwrap_ok_payload(get_response)
            assert_true(isinstance(messages, list), "Messages response data must be list")
            assert_true(any(msg.get("content") == "qa-message" for msg in messages), "Posted message not found")
            results.append(TestResult(name="messages_get_post_delete", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="messages_get_post_delete", passed=False, reason=str(exc)))

        try:
            send_payload = {
                "text": "Hello from QA",
                "speed": 42,
                "fontSize": 2,
                "fontColor": "#ffffff",
                "backgroundColor": "#000000",
                "fontFamily": "Arial",
                "lineHeight": 1.2,
                "opacity": 1,
            }
            send_response = request_json(
                server.base_url,
                "POST",
                "/api/teleprompter/send",
                payload=send_payload,
                default_headers=auth_headers,
            )
            _unwrap_ok_payload(send_response)

            current_response = request_json(
                server.base_url,
                "GET",
                "/api/teleprompter/current",
                default_headers=auth_headers,
            )
            current = _unwrap_ok_payload(current_response)
            assert_true(set(current.keys()) == EXPECTED_TP_KEYS, "Current teleprompter schema mismatch")
            assert_true(current["text"] == send_payload["text"], "Current config did not update after send")

            history_response = request_json(
                server.base_url,
                "GET",
                "/api/teleprompter/history",
                default_headers=auth_headers,
            )
            history = _unwrap_ok_payload(history_response)
            assert_true(isinstance(history, list), "Teleprompter history must be list")
            assert_true(len(history) >= 1, "Teleprompter history should contain at least one item")
            results.append(TestResult(name="teleprompter_send_current_history", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="teleprompter_send_current_history", passed=False, reason=str(exc)))

        try:
            reset_response = request_json(
                server.base_url,
                "POST",
                "/api/teleprompter/reset",
                default_headers=auth_headers,
            )
            reset_data = _unwrap_ok_payload(reset_response)
            assert_true(reset_data.get("status") == "reset", "Reset endpoint did not return reset status")
            assert_true(set(reset_data.get("config", {}).keys()) == EXPECTED_TP_KEYS, "Reset config schema mismatch")
            results.append(TestResult(name="teleprompter_reset", passed=True))
        except Exception as exc:  # noqa: BLE001
            results.append(TestResult(name="teleprompter_reset", passed=False, reason=str(exc)))

    return results


if __name__ == "__main__":
    failures = [result for result in run_api_tests() if not result.passed]
    if failures:
        for failure in failures:
            print(f"FAIL {failure.name}: {failure.reason}")
        raise SystemExit(1)
    print("PASS all api tests")
