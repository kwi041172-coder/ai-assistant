import logging
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import data_analyzer, firebase_service

router = APIRouter()
logger = logging.getLogger(__name__)


class DataRequest(BaseModel):
    date: date
    value: float = Field(allow_inf_nan=False)
    memo: str = Field(default="", max_length=1000)


class DataUpdate(DataRequest):
    pass


def _service_error(exc: Exception) -> HTTPException:
    logger.exception("Data storage request failed: %s", exc)
    if firebase_service.is_firestore_api_disabled(exc):
        return HTTPException(
            status_code=503,
            detail=(
                "Google Cloud Console의 API 라이브러리에서 Cloud Firestore API를 "
                "사용 설정하고, Firebase Console에서 Cloud Firestore 데이터베이스를 "
                "생성한 뒤 다시 시도해 주세요."
            ),
        )
    return HTTPException(status_code=500, detail="데이터를 처리하지 못했습니다.")


@router.post("")
def create_data(req: DataRequest):
    """새 데이터 추가"""
    try:
        return firebase_service.add_data(req.date.isoformat(), req.value, req.memo)
    except Exception as exc:
        raise _service_error(exc) from exc


@router.get("")
def read_all_data():
    """모든 데이터 조회"""
    try:
        return firebase_service.get_all_data()
    except Exception as exc:
        raise _service_error(exc) from exc


@router.put("/{data_id}")
def update_data(data_id: str, req: DataUpdate):
    """데이터 수정"""
    try:
        return firebase_service.update_data(data_id, req.date.isoformat(), req.value, req.memo)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.") from exc
    except Exception as exc:
        raise _service_error(exc) from exc


@router.delete("/{data_id}")
def delete_data(data_id: str):
    """데이터 삭제"""
    try:
        return firebase_service.delete_data(data_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.") from exc
    except Exception as exc:
        raise _service_error(exc) from exc


@router.get("/summary")
def get_summary():
    """데이터 요약 조회 (AI 프롬프트 주입용)"""
    try:
        return data_analyzer.analyze_data()
    except Exception as exc:
        raise _service_error(exc) from exc