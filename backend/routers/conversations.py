import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import storage_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    messages: list["ConversationMessage"] = Field(min_length=1, max_length=200)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20_000)


def _service_error(exc: Exception) -> HTTPException:
    logger.exception("Conversation storage request failed: %s", exc)
    if storage_service.is_firestore_api_disabled(exc):
        return HTTPException(
            status_code=503,
            detail=(
                "Google Cloud Console의 API 라이브러리에서 Cloud Firestore API를 "
                "사용 설정하고, Firebase Console에서 Cloud Firestore 데이터베이스를 "
                "생성한 뒤 다시 시도해 주세요."
            ),
        )
    return HTTPException(status_code=500, detail="대화 기록을 처리하지 못했습니다.")


@router.post("")
def save_conversation(req: ConversationRequest):
    """대화 저장"""
    try:
        return storage_service.save_conversation(
            req.title,
            [message.model_dump() for message in req.messages],
        )
    except Exception as exc:
        raise _service_error(exc) from exc


@router.put("/{conv_id}")
def update_conversation(conv_id: str, req: ConversationRequest):
    """기존 대화의 제목과 메시지 갱신"""
    try:
        return storage_service.update_conversation(
            conv_id,
            req.title,
            [message.model_dump() for message in req.messages],
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.") from exc
    except Exception as exc:
        raise _service_error(exc) from exc


@router.get("")
def get_conversations():
    """대화 목록 조회"""
    try:
        return storage_service.get_all_conversations()
    except Exception as exc:
        raise _service_error(exc) from exc


@router.get("/{conv_id}")
def get_conversation(conv_id: str):
    """특정 대화 조회 (messages 포함)"""
    try:
        conv = storage_service.get_conversation_by_id(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        return conv
    except HTTPException:
        raise
    except Exception as exc:
        raise _service_error(exc) from exc


@router.delete("/{conv_id}")
def delete_conversation(conv_id: str):
    """대화 삭제"""
    try:
        return storage_service.delete_conversation(conv_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.") from exc
    except Exception as exc:
        raise _service_error(exc) from exc


@router.delete("")
def delete_all_conversations():
    """모든 대화 삭제"""
    try:
        return storage_service.delete_all_conversations()
    except Exception as exc:
        raise _service_error(exc) from exc