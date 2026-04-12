import os
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    db_path: str = "data.db"
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    strict_teleprompter_validation: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        origins_raw = os.getenv("CORS_ORIGINS", "*")
        cors_origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
        if not cors_origins:
            cors_origins = ["*"]

        return cls(
            db_path=os.getenv("DB_PATH", "data.db"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "5000")),
            debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"},
            cors_origins=cors_origins,
            strict_teleprompter_validation=(
                os.getenv("TELEPROMPTER_STRICT_VALIDATION", "false").lower()
                in {"1", "true", "yes", "on"}
            ),
        )
