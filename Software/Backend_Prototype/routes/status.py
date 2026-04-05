from datetime import datetime, timezone

from flask import Blueprint, g, jsonify

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
    return _success({
        "Battery": "85%",
        "Temperature": "36.5°C",
        "Humidity": "45%",
    })


@bp.route("/api/status", methods=["GET"])
def get_status():
    return _success(
        {
            "app": "AR-Brille Backend",
            "version": "1.0",
            "health": "ok",
            "endpoints": {
                "messages": "/api/messages",
                "mainInfo": "/api/mainInfo",
                "teleprompter": "/api/teleprompter",
                "teleprompter_send": "/api/teleprompter/send (POST)",
                "teleprompter_history": "/api/teleprompter/history",
                "teleprompter_reset": "/api/teleprompter/reset (POST)",
            },
        }
    )


@bp.route("/api/v1/status", methods=["GET"])
def get_status_v1():
    return get_status()
