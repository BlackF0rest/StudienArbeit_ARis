from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request

bp = Blueprint("messages", __name__)


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


@bp.route("/api/messages", methods=["GET"])
def get_messages():
    messages = current_app.extensions["services"]["message"].get_messages()
    return _success(messages)


@bp.route("/api/messages", methods=["POST"])
def add_message():
    result, error = current_app.extensions["services"]["message"].add_message(request.get_json(silent=True))
    if error:
        return _error(error[0], error[1], {"content": "content is required"}, 400)
    return _success(result)


@bp.route("/api/messages", methods=["DELETE"])
def delete_messages():
    result = current_app.extensions["services"]["message"].delete_messages()
    return _success(result)
