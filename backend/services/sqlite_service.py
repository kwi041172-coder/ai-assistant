import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator


def _database_path() -> Path:
    configured_path = os.getenv("SQLITE_DATABASE_PATH", "local.sqlite3").strip()
    path = Path(configured_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS data (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            value REAL NOT NULL,
            memo TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    return connection


@contextmanager
def _connection() -> Generator[sqlite3.Connection, None, None]:
    connection = _connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def add_data(date: str, value: float, memo: str = "") -> dict[str, str]:
    doc_id = uuid.uuid4().hex
    with _connection() as connection:
        connection.execute(
            "INSERT INTO data (id, date, value, memo, created_at) VALUES (?, ?, ?, ?, ?)",
            (doc_id, date, value, memo, _now()),
        )
    return {"id": doc_id, "message": "데이터가 추가되었습니다."}


def get_all_data() -> list[dict[str, Any]]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT id, date, value, memo, created_at, updated_at "
            "FROM data ORDER BY date DESC, created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def update_data(doc_id: str, date: str, value: float, memo: str = "") -> dict[str, str]:
    with _connection() as connection:
        result = connection.execute(
            "UPDATE data SET date = ?, value = ?, memo = ?, updated_at = ? WHERE id = ?",
            (date, value, memo, _now(), doc_id),
        )
        if result.rowcount == 0:
            raise KeyError(doc_id)
    return {"message": "데이터가 수정되었습니다."}


def delete_data(doc_id: str) -> dict[str, str]:
    with _connection() as connection:
        result = connection.execute("DELETE FROM data WHERE id = ?", (doc_id,))
        if result.rowcount == 0:
            raise KeyError(doc_id)
    return {"message": "데이터가 삭제되었습니다."}


def save_conversation(title: str, messages: list[dict[str, str]]) -> dict[str, str]:
    doc_id = uuid.uuid4().hex
    now = _now()
    with _connection() as connection:
        connection.execute(
            "INSERT INTO conversations (id, title, messages, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, title, json.dumps(messages, ensure_ascii=False), now, now),
        )
    return {"id": doc_id, "message": "대화가 저장되었습니다."}


def update_conversation(
    doc_id: str, title: str, messages: list[dict[str, str]]
) -> dict[str, str]:
    with _connection() as connection:
        result = connection.execute(
            "UPDATE conversations SET title = ?, messages = ?, updated_at = ? WHERE id = ?",
            (title, json.dumps(messages, ensure_ascii=False), _now(), doc_id),
        )
        if result.rowcount == 0:
            raise KeyError(doc_id)
    return {"id": doc_id, "message": "대화가 갱신되었습니다."}


def get_all_conversations() -> list[dict[str, Any]]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT id, title, created_at, updated_at FROM conversations "
            "ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_conversation_by_id(doc_id: str) -> dict[str, Any] | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT id, title, messages, created_at, updated_at "
            "FROM conversations WHERE id = ?",
            (doc_id,),
        ).fetchone()
    if row is None:
        return None
    conversation = dict(row)
    conversation["messages"] = json.loads(conversation["messages"])
    return conversation


def delete_conversation(doc_id: str) -> dict[str, str]:
    with _connection() as connection:
        result = connection.execute("DELETE FROM conversations WHERE id = ?", (doc_id,))
        if result.rowcount == 0:
            raise KeyError(doc_id)
    return {"message": "대화가 삭제되었습니다."}


def delete_all_conversations() -> dict[str, str | int]:
    with _connection() as connection:
        result = connection.execute("DELETE FROM conversations")
    return {"deleted": result.rowcount, "message": "모든 대화가 삭제되었습니다."}
