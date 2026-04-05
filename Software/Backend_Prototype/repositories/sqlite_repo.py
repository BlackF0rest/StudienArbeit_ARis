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
