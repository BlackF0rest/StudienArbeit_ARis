from pathlib import Path

from app import create_app
from config import AppConfig


if __name__ == "__main__":
    config = AppConfig.from_env()
    effective_db_path = Path(config.db_path).expanduser().resolve()
    print(f"[startup] Effective DB_PATH={effective_db_path}")
    app = create_app(config)
    app.run(host=config.host, port=config.port, debug=config.debug)
