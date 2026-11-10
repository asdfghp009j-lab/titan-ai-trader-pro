import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


class AuditLog:
    def __init__(self, path: str):
        self.path = path
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL
            )""")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def write(self, event_type: str, details: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO events(created_at,event_type,details) VALUES(?,?,?)",
                (datetime.now(timezone.utc).isoformat(), event_type, json.dumps(details, ensure_ascii=False)),
            )

    def latest(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,created_at,event_type,details FROM events ORDER BY id DESC LIMIT ?",
                (min(max(limit, 1), 200),),
            ).fetchall()
        return [{"id": r[0], "created_at": r[1], "event_type": r[2], "details": json.loads(r[3])} for r in rows]
