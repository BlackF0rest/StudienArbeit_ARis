from repositories.sqlite_repo import SQLiteRepository


class MessageService:
    def __init__(self, repo: SQLiteRepository):
        self.repo = repo

    def get_messages(self) -> list[dict]:
        return self.repo.get_messages()

    def add_message(self, payload: dict | None) -> tuple[dict | None, tuple[str, str] | None]:
        payload = payload or {}
        content = payload.get("content")
        if not content:
            return None, ("invalid_payload", "no content")

        self.repo.add_message(str(content))
        return {"status": "ok"}, None

    def delete_messages(self) -> dict:
        self.repo.delete_messages()
        return {"status": "all messages deleted"}
