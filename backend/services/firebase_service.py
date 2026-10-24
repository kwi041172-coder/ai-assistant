import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from datetime import datetime
from pathlib import Path


def _get_db():
    if not firebase_admin._apps:
        key_config = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "./firebase-key.json").strip()
        if key_config.startswith("{"):
            try:
                service_account = json.loads(key_config)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "FIREBASE_SERVICE_ACCOUNT_JSON 환경변수의 JSON 형식이 올바르지 않습니다."
                ) from exc
            cred = credentials.Certificate(service_account)
        else:
            key_path = Path(key_config)
            if not key_path.is_absolute():
                key_path = Path(__file__).resolve().parents[1] / key_path
            if not key_path.is_file():
                raise RuntimeError(
                    "Firebase 서비스 계정 파일이 없습니다. "
                    "FIREBASE_SERVICE_ACCOUNT_JSON에 JSON 내용 또는 파일 경로를 설정하세요."
                )
            cred = credentials.Certificate(str(key_path))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def add_data(date: str, value: float, memo: str = ""):
    """새 데이터 추가"""
    doc_ref = _get_db().collection("data").document()
    doc_ref.set({
        "date": date,
        "value": value,
        "memo": memo,
        "created_at": _now(),
    })
    return {"id": doc_ref.id, "message": "데이터가 추가되었습니다."}


def get_all_data():
    """모든 데이터 조회"""
    docs = _get_db().collection("data").order_by(
        "date", direction=firestore.Query.DESCENDING
    ).stream()
    data_list = []
    for doc in docs:
        data = doc.to_dict() or {}
        data["id"] = doc.id
        data_list.append(data)
    return data_list


def update_data(doc_id: str, date: str, value: float, memo: str = ""):
    """데이터 수정"""
    ref = _get_db().collection("data").document(doc_id)
    if not ref.get().exists:
        raise KeyError(doc_id)
    ref.update({
        "date": date,
        "value": value,
        "memo": memo,
        "updated_at": _now(),
    })
    return {"message": "데이터가 수정되었습니다."}


def delete_data(doc_id: str):
    """데이터 삭제"""
    ref = _get_db().collection("data").document(doc_id)
    if not ref.get().exists:
        raise KeyError(doc_id)
    ref.delete()
    return {"message": "데이터가 삭제되었습니다."}


def save_conversation(title: str, messages: list):
    """대화 저장"""
    doc_ref = _get_db().collection("conversations").document()
    doc_ref.set({
        "title": title,
        "messages": messages,
        "created_at": _now(),
        "updated_at": _now(),
    })
    return {"id": doc_ref.id, "message": "대화가 저장되었습니다."}


def update_conversation(doc_id: str, title: str, messages: list):
    """기존 대화 갱신"""
    ref = _get_db().collection("conversations").document(doc_id)
    if not ref.get().exists:
        raise KeyError(doc_id)
    ref.update({
        "title": title,
        "messages": messages,
        "updated_at": _now(),
    })
    return {"id": doc_id, "message": "대화가 갱신되었습니다."}


def get_all_conversations():
    """대화 목록 조회 (messages 제외)"""
    docs = list(_get_db().collection("conversations").stream())
    conv_list = []
    for doc in docs:
        data = doc.to_dict() or {}
        data["id"] = doc.id
        data.pop("messages", None)
        conv_list.append(data)
    return sorted(
        conv_list,
        key=lambda conversation: conversation.get("updated_at", conversation.get("created_at", "")),
        reverse=True,
    )


def get_conversation_by_id(doc_id: str):
    """특정 대화 조회 (messages 포함)"""
    doc = _get_db().collection("conversations").document(doc_id).get()
    if doc.exists:
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data
    return None


def delete_conversation(doc_id: str):
    """대화 삭제"""
    ref = _get_db().collection("conversations").document(doc_id)
    if not ref.get().exists:
        raise KeyError(doc_id)
    ref.delete()
    return {"message": "대화가 삭제되었습니다."}


def delete_all_conversations():
    """모든 대화 삭제"""
    db = _get_db()
    docs = list(db.collection("conversations").stream())
    for offset in range(0, len(docs), 450):
        batch = db.batch()
        for doc in docs[offset:offset + 450]:
            batch.delete(doc.reference)
        batch.commit()
    return {"deleted": len(docs), "message": "모든 대화가 삭제되었습니다."}