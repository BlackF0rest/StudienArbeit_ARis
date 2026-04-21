from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify

from hardware.pinmap import PINMAP_RESPONSE

bp = Blueprint("status", __name__)


def _success(data, status_code: int = 200):
    return (
        jsonify(
            {
                "ok": True,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": g.trace_id,
            }
        ),
        status_code,
    )


@bp.route("/api/mainInfo", methods=["GET"])
def get_main_info():
    return _success(
        {
            "battery_percent": 85,
            "temperature_c": 36.5,
            "humidity_percent": 45,
            "battery_unit": "%",
            "temperature_unit": "°C",
            "humidity_unit": "%",
            "pinmap": PINMAP_RESPONSE,
        }
    )


@bp.route("/api/status", methods=["GET"])
def get_status():
    sensor_service = current_app.extensions.get("services", {}).get("sensor")
    hardware_ready = (
        sensor_service.get_hardware_readiness()
        if sensor_service is not None
        else {
            "ok": False,
            "error": "Sensor service is not registered",
        }
    )

    return _success(
        {
            "app": "AR-Brille Backend",
            "version": "1.0",
            "health": "ok",
            "handshake": {
                "protocol": "status-handshake-v1",
                "device": {
                    "device_id": "ar-brille-backend",
                    "friendly_name": "AR Brille",
                    "firmware_version": "1.0.0",
                    "app_version": "1.0",
                    "capabilities": [
                        "teleprompter",
                        "messages",
                        "sensors",
                        "navigation",
                    ],
                },
            },
            "hardware_ready": hardware_ready,
            "endpoints": {
                "auth_pairing_start": "/api/auth/pairing/start (POST)",
                "auth_pairing_exchange": "/api/auth/pairing/exchange (POST)",
                "auth_revoke": "/api/auth/session/revoke (POST)",
                "messages": "/api/messages",
                "mainInfo": "/api/mainInfo",
                "teleprompter": "/api/teleprompter",
                "teleprompter_send": "/api/teleprompter/send (POST)",
                "teleprompter_history": "/api/teleprompter/history",
                "teleprompter_reset": "/api/teleprompter/reset (POST)",
                "sensors": "/api/sensors",
                "navigation_current": "/api/navigation/current",
                "debug_diagnostics": "/api/debug/diagnostics" if current_app.config["APP_CONFIG"].debug else None,
            },
            "pinmap": PINMAP_RESPONSE,
        }
    )


@bp.route("/api/v1/status", methods=["GET"])
def get_status_v1():
    return get_status()


@bp.route("/api/sensors", methods=["GET"])
def get_sensor_snapshot():
    sensor_service = current_app.extensions.get("services", {}).get("sensor")

    if sensor_service is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "sensor_service_unavailable",
                        "message": "Sensor service is not registered",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trace_id": g.trace_id,
                }
            ),
            503,
        )

    return _success(sensor_service.get_snapshot())


@bp.route("/api/debug/diagnostics", methods=["GET"])
def get_debug_diagnostics():
    now = datetime.now(timezone.utc).isoformat()
    return (
        jsonify(
            {
                "panels": {
                    "pc_link": {
                        "pc_link": {
                            "active": False,
                            "sessions": [],
                        },
                        "stream_metrics": {
                            "connected": False,
                            "reconnect_attempts": 0,
                            "quality": "medium",
                            "avg_bandwidth_mbps": None,
                            "avg_frame_drop_ratio": None,
                            "onboard_only_mode": False,
                            "last_updated": now,
                        },
                        "overlay_contract": {
                            "contract_version": "1.0",
                            "coordinate_space": "normalized",
                            "safe_area": {"x": 0, "y": 0, "width": 1, "height": 1},
                            "z_order": ["streamed-scene", "streamed-overlay", "onboard-hud"],
                            "last_synced_at": now,
                        },
                    }
                },
                "timestamp": now,
                "trace_id": g.trace_id,
            }
        ),
        200,
    )
