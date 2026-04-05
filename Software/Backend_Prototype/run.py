from app import create_app
from config import AppConfig


if __name__ == "__main__":
    config = AppConfig.from_env()
    app = create_app(config)
    app.run(host=config.host, port=config.port, debug=config.debug)
