import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from openai import OpenAIError
from pydantic import BaseModel, Field

from ..services import data_analyzer
from ..services.openai_service import OpenAIConfigurationError, chat_with_context

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=100)


@router.post("")
def chat(req: ChatRequest) -> dict[str, str | dict]:
    """AI 대화 (데이터 요약 컨텍스트 주입)"""
    try:
        summary = data_analyzer.analyze_data()
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

    return {"response": answer, "summary": summary}