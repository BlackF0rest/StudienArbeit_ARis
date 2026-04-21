import logging
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import AppConfig
from repositories.sqlite_repo import SQLiteRepository
from routes.messages import bp as messages_bp
from routes.navigation import bp as navigation_bp
from routes.status import bp as status_bp
from routes.teleprompter import bp as teleprompter_bp
from services.message_service import MessageService
from services.navigation_service import NavigationService
from services.sensor_service import SensorService
from services.teleprompter_service import TeleprompterService


def create_app(config: AppConfig | None = None) -> Flask:
    app_config = config or AppConfig.from_env()

    app = Flask(__name__)
    app.config["APP_CONFIG"] = app_config

    CORS(app, resources={r"/*": {"origins": app_config.cors_origins}})

    logging.basicConfig(
        level=logging.DEBUG if app_config.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    repo = SQLiteRepository(app_config.db_path)
    repo.init_db()

    sensor_service = SensorService()
    app.extensions["services"] = {
        "message": MessageService(repo),
        "teleprompter": TeleprompterService(
            repo=repo,
            strict_validation=app_config.strict_teleprompter_validation,
        ),
        "sensor": sensor_service,
        "navigation": NavigationService(sensor_service),
    }

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

    app.register_blueprint(messages_bp)
    app.register_blueprint(teleprompter_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(navigation_bp)

    return app


if __name__ == "__main__":
    cfg = AppConfig.from_env()
    app = create_app(cfg)
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
