from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request

bp = Blueprint("teleprompter", __name__)


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


@bp.route("/api/teleprompter", methods=["GET"])
def get_teleprompter_config():
    data = current_app.extensions["services"]["teleprompter"].get_config()
    return _success(data)


@bp.route("/api/teleprompter/current", methods=["GET"])
def get_current_teleprompter():
    data = current_app.extensions["services"]["teleprompter"].get_current()
    return _success(data)


@bp.route("/api/teleprompter/send", methods=["POST"])
def send_to_glasses():
    data, error = current_app.extensions["services"]["teleprompter"].send_to_glasses(
        request.get_json(silent=True)
    )
    if error:
        return _error(error["code"], error["message"], error.get("details"), 400)
    return _success(data)


@bp.route("/api/teleprompter/history", methods=["GET"])
def get_teleprompter_history():
    data = current_app.extensions["services"]["teleprompter"].get_history()
    return _success(data)


@bp.route("/api/teleprompter/reset", methods=["POST"])
def reset_teleprompter():
    data = current_app.extensions["services"]["teleprompter"].reset()
    return _success(data)


@bp.route("/api/v1/teleprompter/send", methods=["POST"])
def send_to_glasses_alias():
    return send_to_glasses()
