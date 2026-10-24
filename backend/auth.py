import os
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


def require_app_password(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    expected = os.getenv("APP_ACCESS_PASSWORD")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="앱 접속 비밀번호가 설정되지 않았습니다. APP_ACCESS_PASSWORD를 설정하세요.",
        )
    supplied = credentials.credentials if credentials else ""
    if not secrets.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=401,
            detail="앱 접속 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
