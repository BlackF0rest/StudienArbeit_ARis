from __future__ import annotations
from datetime import datetime

from repositories.sqlite_repo import SQLiteRepository
from schemas.teleprompter_schema import validate_teleprompter_payload

DEFAULT_TELEPROMPTER_CONFIG = {
    "text": "Willkommen zur AR-Brille!\n\nDies ist der Standard-Text.\nKlicke auf 'An AR-Brille senden' in der Test-Seite.",
    "speed": 30,
    "fontSize": 2,
    "fontColor": "#0f0",
    "backgroundColor": "#000",
    "fontFamily": "Courier New",
    "lineHeight": 1.5,
    "opacity": 1,
}

RESET_TELEPROMPTER_CONFIG = {
    "text": "Willkommen zur AR-Brille!\n\nDies ist der Standard-Text.",
    "speed": 30,
    "fontSize": 2,
    "fontColor": "#0f0",
    "backgroundColor": "#000",
    "fontFamily": "Courier New",
    "lineHeight": 1.5,
    "opacity": 1,
}


class TeleprompterService:
    def __init__(self, repo: SQLiteRepository, strict_validation: bool = False):
        self.repo = repo
        self.strict_validation = strict_validation
        self.current_config = DEFAULT_TELEPROMPTER_CONFIG.copy()

    def get_config(self) -> dict:
        return self.current_config

    def get_current(self) -> dict:
        latest = self.repo.get_current_teleprompter()
        if latest:
            self.current_config = latest
        return self.current_config

    def send_to_glasses(self, payload: dict | None) -> tuple[dict | None, dict | None]:
        cleaned, errors, warnings = validate_teleprompter_payload(
            payload=payload,
            defaults=self.current_config,
            strict=self.strict_validation,
        )

        if errors:
            return None, {
                "code": "invalid_teleprompter_payload",
                "message": "Payload validation failed",
                "details": errors,
            }

        assert cleaned is not None
        self.current_config = cleaned
        self.repo.save_teleprompter_config(cleaned)
        timestamp = datetime.now().strftime("%H:%M:%S")

        response = {
            "status": "success",
            "message": "Zur AR-Brille gesendet",
            "timestamp": timestamp,
        }
        if warnings:
            response["warnings"] = warnings
        return response, None

    def get_history(self) -> list[dict]:
        return self.repo.get_teleprompter_history(limit=10)

    def reset(self) -> dict:
        self.current_config = RESET_TELEPROMPTER_CONFIG.copy()
        return {
            "status": "reset",
            "config": self.current_config,
        }
