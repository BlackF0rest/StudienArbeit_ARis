from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request

bp = Blueprint("auth", __name__)


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


@bp.route('/api/auth/pairing/start', methods=['POST'])
def start_pairing():
    payload = request.get_json(silent=True) or {}
    device_id = str(payload.get('device_id', '')).strip()
    device_name = payload.get('device_name')

    if not device_id:
        return _error('invalid_payload', 'device_id is required', {'field': 'device_id'})

    result = current_app.extensions['services']['auth'].start_pairing(device_id=device_id, device_name=device_name)
    return _success(result, 201)


@bp.route('/api/auth/pairing/exchange', methods=['POST'])
def exchange_pairing():
    payload = request.get_json(silent=True) or {}
    device_id = str(payload.get('device_id', '')).strip()
    pairing_code = str(payload.get('pairing_code', '')).strip()

    if not device_id or not pairing_code:
        return _error(
            'invalid_payload',
            'device_id and pairing_code are required',
            {'required': ['device_id', 'pairing_code']},
        )

    result, error = current_app.extensions['services']['auth'].exchange_pairing_code(
        device_id=device_id,
        pairing_code=pairing_code,
    )
    if error:
        return _error(error['code'], error['message'], status_code=401)

    return _success(result, 201)


@bp.route('/api/auth/session/revoke', methods=['POST'])
def revoke_session():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return _error('unauthorized', 'Bearer token is required', status_code=401)

    token = auth_header.removeprefix('Bearer ').strip()
    revoked = current_app.extensions['services']['auth'].revoke_token(token)
    if not revoked:
        return _error('token_invalid', 'Token is invalid or already expired', status_code=401)

    return _success({'status': 'revoked'})
