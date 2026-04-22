import logging
import uuid
from datetime import datetime, timezone

from flask import Flask, g, has_request_context, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import AppConfig
from repositories.sqlite_repo import SQLiteRepository
from routes.auth import bp as auth_bp
from routes.messages import bp as messages_bp
from routes.navigation import bp as navigation_bp
from routes.settings import bp as settings_bp
from routes.status import bp as status_bp
from routes.teleprompter import bp as teleprompter_bp
from services.auth_service import AuthService
from services.message_service import MessageService
from services.navigation_service import NavigationService
from services.sensor_service import SensorService
from services.device_settings_service import DeviceSettingsService
from services.rate_limiter import InMemoryRateLimiter
from services.teleprompter_service import TeleprompterService


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = getattr(g, "trace_id", "-") if has_request_context() else "-"
        if not hasattr(record, "client_type"):
            record.client_type = request.headers.get("X-Client-Type", "-") if has_request_context() else "-"
        return True


def create_app(config: AppConfig | None = None) -> Flask:
    app_config = config or AppConfig.from_env()

    app = Flask(__name__)
    app.config["APP_CONFIG"] = app_config

    CORS(app, resources={r"/*": {"origins": app_config.cors_origins}})

    logging.basicConfig(
        level=logging.DEBUG if app_config.debug else logging.INFO,
        format="%(asctime)s %(levelname)s [trace_id=%(trace_id)s client=%(client_type)s] %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestContextFilter())

    repo = SQLiteRepository(app_config.db_path)
    repo.init_db()

    sensor_service = SensorService()
    auth_service = AuthService(
        repo=repo,
        pairing_ttl_seconds=app_config.auth_pairing_ttl_seconds,
        token_ttl_days=app_config.auth_token_ttl_days,
    )
    app.extensions["services"] = {
        "message": MessageService(repo),
        "teleprompter": TeleprompterService(
            repo=repo,
            strict_validation=app_config.strict_teleprompter_validation,
        ),
        "sensor": sensor_service,
        "navigation": NavigationService(sensor_service),
        "auth": auth_service,
        "settings": DeviceSettingsService(repo),
    }
    app.extensions["write_rate_limiter"] = InMemoryRateLimiter(
        limit=app_config.write_rate_limit_per_minute,
        window_seconds=60,
    )

    hardware_readiness = sensor_service.get_hardware_readiness()
    app.logger.info(
        "hardware_health",
        extra={
            "hardware_ready": hardware_readiness["ok"],
            "gpio_initialized": hardware_readiness["gpio"]["initialized"],
            "gpio_error": hardware_readiness["gpio"]["error"],
            "i2c_initialized": hardware_readiness["i2c"]["initialized"],
            "i2c_error": hardware_readiness["i2c"]["error"],
            "i2c_device_path": hardware_readiness["i2c"]["device_path"],
            "i2c_device_path_exists": hardware_readiness["i2c"]["device_path_exists"],
        },
    )

    @app.before_request
    def before_request():
        g.trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        g.request_start = datetime.now(timezone.utc)
        app.logger.info(
            "request_start",
            extra={
                "trace_id": g.trace_id,
                "client_type": request.headers.get("X-Client-Type", "-"),
                "method": request.method,
                "path": request.path,
            },
        )

        is_companion = request.headers.get("X-Client-Type", "").lower() == "companion"
        if is_companion and not any(
            request.path.startswith(prefix) for prefix in app_config.companion_whitelist_paths
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": {
                            "code": "endpoint_not_whitelisted",
                            "message": "Companion client cannot access this endpoint",
                            "details": {"path": request.path},
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "trace_id": g.trace_id,
                    }
                ),
                403,
            )

        if request.path.startswith("/api/debug") and not app_config.debug:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": {
                            "code": "debug_disabled",
                            "message": "Debug endpoints are disabled in production",
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "trace_id": g.trace_id,
                    }
                ),
                404,
            )

        needs_auth = any(request.path.startswith(prefix) for prefix in app_config.auth_required_paths)
        is_auth_bootstrap = request.path.startswith("/api/auth/pairing")

        if needs_auth and not is_auth_bootstrap:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": {
                                "code": "unauthorized",
                                "message": "Bearer token is required",
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "trace_id": g.trace_id,
                        }
                    ),
                    401,
                )

            raw_token = auth_header.removeprefix("Bearer ").strip()
            token_meta = auth_service.validate_token(raw_token)
            if not token_meta:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": {
                                "code": "token_invalid",
                                "message": "Token is invalid or expired",
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "trace_id": g.trace_id,
                        }
                    ),
                    401,
                )
            g.auth_device_id = token_meta["device_id"]
            g.auth_token_id = token_meta["token_id"]

        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.path.startswith("/api/"):
            limiter = app.extensions["write_rate_limiter"]
            rate_key = f"{request.remote_addr}:{request.path}"
            allowed, retry_after = limiter.allow(rate_key)
            if not allowed:
                response = jsonify(
                    {
                        "ok": False,
                        "error": {
                            "code": "rate_limited",
                            "message": "Too many write requests",
                            "details": {"retry_after_seconds": retry_after},
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "trace_id": g.trace_id,
                    }
                )
                response.headers["Retry-After"] = str(retry_after)
                return response, 429

    @app.after_request
    def after_request(response):
        duration_ms = int((datetime.now(timezone.utc) - g.request_start).total_seconds() * 1000)
        response.headers["X-Trace-ID"] = g.trace_id
        app.logger.info(
            "request",
            extra={
                "trace_id": g.trace_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception):
        if isinstance(exc, HTTPException):
            if exc.code == 404:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": {
                                "code": "not_found",
                                "message": "Route not found",
                                "details": {"path": request.path},
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "trace_id": getattr(g, "trace_id", "n/a"),
                        }
                    ),
                    404,
                )

            return (
                jsonify(
                    {
                        "ok": False,
                        "error": {
                            "code": exc.name.lower().replace(" ", "_"),
                            "message": exc.description,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "trace_id": getattr(g, "trace_id", "n/a"),
                    }
                ),
                exc.code or 500,
            )

        app.logger.exception("unhandled_error", extra={"trace_id": getattr(g, "trace_id", "n/a")})
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "internal_error",
                        "message": "An internal error occurred",
                        "details": {"exception": str(exc)},
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trace_id": getattr(g, "trace_id", "n/a"),
                }
            ),
            500,
        )

    app.register_blueprint(auth_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(teleprompter_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(navigation_bp)

    return app


if __name__ == "__main__":
    cfg = AppConfig.from_env()
    app = create_app(cfg)
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
