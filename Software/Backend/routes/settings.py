from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request

bp = Blueprint("settings", __name__)


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


def _error(code: str, message: str, details=None, status_code: int = 400):
    return (
        jsonify(
            {
                "ok": False,
                "error": {"code": code, "message": message, "details": details or {}},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": g.trace_id,
            }
        ),
        status_code,
    )


@bp.route("/api/settings/device", methods=["GET"])
def get_device_settings():
    settings_service = current_app.extensions.get("services", {}).get("settings")
    if settings_service is None:
        return _error(
            code="settings_service_unavailable",
            message="Settings service is not registered",
            status_code=503,
        )

    return _success(settings_service.get_settings())


@bp.route("/api/settings/device", methods=["PATCH"])
def patch_device_settings():
    settings_service = current_app.extensions.get("services", {}).get("settings")
    if settings_service is None:
        return _error(
            code="settings_service_unavailable",
            message="Settings service is not registered",
            status_code=503,
        )

    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        return _error(
            code="invalid_payload",
            message="Request body must be a JSON object",
            status_code=400,
        )

    return _success(settings_service.update_settings(payload))


@bp.route("/health", methods=["GET"])
def health():
    sensor_service = current_app.extensions.get("services", {}).get("sensor")
    hardware_readiness = (
        sensor_service.get_hardware_readiness()
        if sensor_service is not None
        else {"ok": False, "error": "Sensor service is not registered"}
    )

    return _success(
        {
            "status": "ok",
            "service": "backend",
            "hardware_ready": bool(hardware_readiness.get("ok", False)),
        }
    )
