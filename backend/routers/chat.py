import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from openai import OpenAIError
from pydantic import BaseModel, Field

from ..services import data_analyzer, firebase_service
from ..services.openai_service import OpenAIConfigurationError, chat_with_context

router = APIRouter()
logger = logging.getLogger(__name__)
FIRESTORE_WARNING = (
    "Firestore에서 개인 데이터 요약을 가져오지 못해 데이터 없이 답변했습니다. "
    "대화도 저장되지 않았습니다. Cloud Firestore API를 활성화하고 데이터베이스를 "
    "생성한 뒤 다시 시도해 주세요."
)
SUMMARY_WARNING = (
    "개인 데이터 요약을 가져오지 못해 데이터 없이 답변했습니다. "
    "대화 기록도 저장되지 않았습니다. 서버의 Firestore 설정과 접근 권한을 확인해 주세요."
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=100)


@router.post("")
def chat(req: ChatRequest) -> dict[str, str | dict | None]:
    """AI 대화 (데이터 요약 컨텍스트 주입)"""
    summary = None
    warning = None
    try:
        summary = data_analyzer.analyze_data()
    except Exception as exc:
        logger.exception("Data summary unavailable; continuing chat without personal data")
        warning = (
            FIRESTORE_WARNING
            if firebase_service.is_firestore_api_disabled(exc)
            else SUMMARY_WARNING
        )

    try:
        answer = chat_with_context(
            req.message,
            summary,
            [message.model_dump() for message in req.messages],
        )
    except OpenAIConfigurationError as exc:
        logger.error("OpenAI service is not configured: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIError as exc:
        logger.exception("OpenAI chat request failed")
        raise HTTPException(
            status_code=502,
            detail="OpenAI API 요청에 실패했습니다. 백엔드 로그와 사용량 한도를 확인해 주세요.",
        ) from exc
    except Exception as exc:
        logger.exception("Failed to create chat response")
        raise HTTPException(status_code=500, detail="채팅 응답을 생성하지 못했습니다.") from exc

    return {"response": answer, "summary": summary, "warning": warning}