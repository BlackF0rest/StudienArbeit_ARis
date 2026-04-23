import os
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data.db"


@dataclass
class AppConfig:
    db_path: str = str(DEFAULT_DB_PATH)
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    strict_teleprompter_validation: bool = False
    auth_pairing_ttl_seconds: int = 300
    auth_token_ttl_days: int = 30
    auth_required_paths: list[str] = field(default_factory=lambda: ["/api/messages", "/api/teleprompter", "/api/navigation", "/api/sensors", "/api/settings"])
    companion_whitelist_paths: list[str] = field(default_factory=lambda: [
        "/api/status",
        "/api/mainInfo",
        "/api/messages",
        "/api/teleprompter",
        "/api/navigation/current",
        "/api/sensors",
        "/api/settings/device",
        "/health",
        "/api/auth/pairing/start",
        "/api/auth/pairing/exchange",
        "/api/auth/session/revoke",
    ])
    write_rate_limit_per_minute: int = 60

    @classmethod
    def from_env(cls) -> "AppConfig":
        origins_raw = os.getenv("CORS_ORIGINS", "*")
        cors_origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
        if not cors_origins:
            cors_origins = ["*"]

        auth_required_paths = [
            part.strip() for part in os.getenv("AUTH_REQUIRED_PATHS", "/api/messages,/api/teleprompter,/api/navigation,/api/sensors,/api/settings").split(",") if part.strip()
        ]
        companion_whitelist_paths = [
            part.strip() for part in os.getenv(
                "COMPANION_WHITELIST_PATHS",
                "/api/status,/api/mainInfo,/api/messages,/api/teleprompter,/api/navigation/current,/api/sensors,/api/settings/device,/health,/api/auth/pairing/start,/api/auth/pairing/exchange,/api/auth/session/revoke",
            ).split(",") if part.strip()
        ]

        return cls(
            db_path=os.getenv("DB_PATH", str(DEFAULT_DB_PATH)),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "5000")),
            debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"},
            cors_origins=cors_origins,
            strict_teleprompter_validation=(
                os.getenv("TELEPROMPTER_STRICT_VALIDATION", "false").lower()
                in {"1", "true", "yes", "on"}
            ),
            auth_pairing_ttl_seconds=int(os.getenv("AUTH_PAIRING_TTL_SECONDS", "300")),
            auth_token_ttl_days=int(os.getenv("AUTH_TOKEN_TTL_DAYS", "30")),
            auth_required_paths=auth_required_paths,
            companion_whitelist_paths=companion_whitelist_paths,
            write_rate_limit_per_minute=int(os.getenv("WRITE_RATE_LIMIT_PER_MINUTE", "60")),
        )
