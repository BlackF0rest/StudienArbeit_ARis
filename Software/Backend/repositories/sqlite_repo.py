import json
import sqlite3
from typing import Any


class SQLiteRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS messages1 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS teleprompter_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    speed REAL,
                    fontSize REAL,
                    fontColor TEXT,
                    backgroundColor TEXT,
                    fontFamily TEXT,
                    lineHeight REAL,
                    opacity REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS pairing_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    device_name TEXT,
                    code_hash TEXT NOT NULL,
                    code_salt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS device_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    token_prefix TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    token_salt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    expires_at TEXT NOT NULL,
                    revoked_reason TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    revoked_at TEXT
                )
                """
            )
            conn.commit()

    def get_messages(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, content FROM messages1 ORDER BY id DESC")
            rows = c.fetchall()
        return [{"id": row[0], "content": row[1]} for row in rows]

    def add_message(self, content: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO messages1 (content) VALUES (?)", (content,))
            conn.commit()

    def delete_messages(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM messages1")
            conn.commit()

    def save_teleprompter_config(self, config: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO teleprompter_history
                (text, speed, fontSize, fontColor, backgroundColor, fontFamily, lineHeight, opacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config["text"],
                    config["speed"],
                    config["fontSize"],
                    config["fontColor"],
                    config["backgroundColor"],
                    config["fontFamily"],
                    config["lineHeight"],
                    config["opacity"],
                ),
            )
            conn.commit()

    def get_teleprompter_history(self, limit: int = 10) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, text, speed, fontSize, timestamp
                FROM teleprompter_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = c.fetchall()
        return [
            {
                "id": row[0],
                "text": f"{row[1][:50]}..." if row[1] else "",
                "speed": row[2],
                "fontSize": row[3],
                "timestamp": row[4],
            }
            for row in rows
        ]

    def get_current_teleprompter(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT text, speed, fontSize, fontColor, backgroundColor, fontFamily, lineHeight, opacity
                FROM teleprompter_history
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = c.fetchone()

        if not row:
            return None

        return {
            "text": row[0],
            "speed": row[1],
            "fontSize": row[2],
            "fontColor": row[3],
            "backgroundColor": row[4],
            "fontFamily": row[5],
            "lineHeight": row[6],
            "opacity": row[7],
        }


    def create_pairing_session(
        self,
        device_id: str,
        device_name: str | None,
        code_hash: str,
        code_salt: str,
        expires_at,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO pairing_sessions (device_id, device_name, code_hash, code_salt, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (device_id, device_name, code_hash, code_salt, expires_at.isoformat()),
            )
            conn.commit()
            return int(c.lastrowid)

    def get_latest_open_pairing_session(self, device_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, code_hash, code_salt, expires_at
                FROM pairing_sessions
                WHERE device_id = ? AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (device_id,),
            )
            row = c.fetchone()
        if not row:
            return None
        return {"id": row[0], "code_hash": row[1], "code_salt": row[2], "expires_at": row[3]}

    def close_pairing_session(self, session_id: int, status: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE pairing_sessions SET status = ? WHERE id = ?", (status, session_id))
            conn.commit()

    def revoke_tokens_for_other_devices(self, device_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                UPDATE auth_tokens
                SET status = 'revoked', revoked_reason = 'device_switch', revoked_at = CURRENT_TIMESTAMP
                WHERE status = 'active' AND device_id != ?
                """,
                (device_id,),
            )
            conn.commit()

    def store_auth_token(
        self,
        token_id: str,
        device_id: str,
        token_plain: str,
        token_hash: str,
        token_salt: str,
        expires_at,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO auth_tokens (token_id, device_id, token_prefix, token_hash, token_salt, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (token_id, device_id, token_plain[:10], token_hash, token_salt, expires_at.isoformat()),
            )
            conn.commit()

    def get_active_tokens_by_prefix(self, token_prefix: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT token_id, device_id, token_hash, token_salt, expires_at
                FROM auth_tokens
                WHERE token_prefix = ? AND status = 'active'
                """,
                (token_prefix,),
            )
            rows = c.fetchall()
        return [
            {
                "token_id": row[0],
                "device_id": row[1],
                "token_hash": row[2],
                "token_salt": row[3],
                "expires_at": row[4],
            }
            for row in rows
        ]

    def revoke_token(self, token_id: str, reason: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                UPDATE auth_tokens
                SET status = 'revoked', revoked_reason = ?, revoked_at = CURRENT_TIMESTAMP
                WHERE token_id = ?
                """,
                (reason, token_id),
            )
            conn.commit()

    def get_device_settings(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT payload FROM device_settings WHERE id = 1")
            row = c.fetchone()

        if not row:
            return None

        try:
            parsed = json.loads(row[0])
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    def save_device_settings(self, payload: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            serialized = json.dumps(payload)
            c.execute(
                """
                INSERT INTO device_settings (id, payload)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (serialized,),
            )
            conn.commit()
