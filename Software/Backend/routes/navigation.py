from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify

bp = Blueprint("navigation", __name__)


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


@bp.route("/api/navigation/current", methods=["GET"])
def get_current_navigation_snapshot():
    navigation_service = current_app.extensions.get("services", {}).get("navigation")

    if navigation_service is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "navigation_service_unavailable",
                        "message": "Navigation service is not registered",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trace_id": g.trace_id,
                }
            ),
            503,
        )

    return _success(navigation_service.get_current_snapshot())
