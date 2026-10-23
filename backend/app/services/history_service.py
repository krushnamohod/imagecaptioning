"""SQLite persistence for generated caption history."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterator


class HistoryRepository:
    """Small connection-per-operation SQLite repository."""

    def __init__(self, database_path: Path | str):
        self.database_path = Path(database_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.database_path), timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the history table and index if absent."""
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS caption_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_caption TEXT NOT NULL,
                    generated_caption TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    language TEXT NOT NULL,
                    writing_style TEXT NOT NULL,
                    visual_template TEXT,
                    created_at_utc TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_caption_history_created "
                "ON caption_history (created_at_utc DESC, id DESC)"
            )

    @staticmethod
    def _record(row: sqlite3.Row | None) -> dict | None:
        return dict(row) if row is not None else None

    def insert(
        self,
        *,
        base_caption: str,
        generated_caption: str,
        platform: str,
        language: str,
        writing_style: str,
        visual_template: str | None,
    ) -> dict:
        """Insert a completed generation and return the stored record."""
        timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        with self._connection() as connection:
            cursor = connection.execute(
                """INSERT INTO caption_history
                   (base_caption, generated_caption, platform, language, writing_style,
                    visual_template, created_at_utc)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (base_caption, generated_caption, platform, language, writing_style, visual_template, timestamp),
            )
            row = connection.execute(
                "SELECT * FROM caption_history WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return self._record(row)  # type: ignore[return-value]

    def list(self, *, limit: int, offset: int) -> tuple[list[dict], int]:
        with self._connection() as connection:
            total = connection.execute("SELECT COUNT(*) FROM caption_history").fetchone()[0]
            rows = connection.execute(
                """SELECT * FROM caption_history
                   ORDER BY created_at_utc DESC, id DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows], total

    def get(self, record_id: int) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM caption_history WHERE id = ?", (record_id,)
            ).fetchone()
            return self._record(row)

    def delete(self, record_id: int) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM caption_history WHERE id = ?", (record_id,)
            )
            return cursor.rowcount > 0
