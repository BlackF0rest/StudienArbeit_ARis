import sqlite3
from typing import Any, Optional


class SQLiteRepository:
    def __init__(self, db_path: str = "teleprompter.db") -> None:
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
            conn.commit()

    def get_messages(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, content FROM messages1 ORDER BY id DESC")
            return [{"id": row[0], "content": row[1]} for row in c.fetchall()]

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
                    config.get("text"),
                    config.get("speed"),
                    config.get("fontSize"),
                    config.get("fontColor"),
                    config.get("backgroundColor"),
                    config.get("fontFamily"),
                    config.get("lineHeight"),
                    config.get("opacity"),
                ),
            )
            conn.commit()

    def get_teleprompter_history(self, limit: int = 50) -> list[dict[str, Any]]:
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
            return [
                {
                    "id": row[0],
                    "text": f"{row[1][:100]}..." if row[1] and len(row[1]) > 100 else (row[1] or ""),
                    "speed": row[2],
                    "fontSize": row[3],
                    "timestamp": row[4],
                }
                for row in c.fetchall()
            ]

    def get_current_teleprompter(self) -> Optional[dict[str, Any]]:
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
            if row:
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
            return None
