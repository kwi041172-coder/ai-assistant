import importlib
import os
from types import ModuleType
from typing import Any


def _storage_backend() -> ModuleType:
    name = os.getenv("STORAGE_BACKEND", "firestore").strip().lower()
    if name == "sqlite":
        if os.getenv("VERCEL") == "1":
            raise RuntimeError("SQLite storage is for local development only; use Firestore on Vercel.")
        module_name = ".sqlite_service"
    elif name == "firestore":
        module_name = ".firebase_service"
    else:
        raise RuntimeError("STORAGE_BACKEND must be either 'sqlite' or 'firestore'.")
    return importlib.import_module(module_name, __package__)


def add_data(date: str, value: float, memo: str = "") -> dict[str, str]:
    return _storage_backend().add_data(date, value, memo)


def get_all_data() -> list[dict[str, Any]]:
    return _storage_backend().get_all_data()


def update_data(date_id: str, date: str, value: float, memo: str = "") -> dict[str, str]:
    return _storage_backend().update_data(date_id, date, value, memo)


def delete_data(date_id: str) -> dict[str, str]:
    return _storage_backend().delete_data(date_id)


def save_conversation(title: str, messages: list[dict[str, str]]) -> dict[str, str]:
    return _storage_backend().save_conversation(title, messages)


def update_conversation(
    conversation_id: str, title: str, messages: list[dict[str, str]]
) -> dict[str, str]:
    return _storage_backend().update_conversation(conversation_id, title, messages)


def get_all_conversations() -> list[dict[str, Any]]:
    return _storage_backend().get_all_conversations()


def get_conversation_by_id(conversation_id: str) -> dict[str, Any] | None:
    return _storage_backend().get_conversation_by_id(conversation_id)


def delete_conversation(conversation_id: str) -> dict[str, str]:
    return _storage_backend().delete_conversation(conversation_id)


def delete_all_conversations() -> dict[str, str | int]:
    return _storage_backend().delete_all_conversations()


def is_firestore_api_disabled(exc: Exception) -> bool:
    backend_name = os.getenv("STORAGE_BACKEND", "firestore").strip().lower()
    if backend_name == "sqlite":
        return False
    return _storage_backend().is_firestore_api_disabled(exc)
