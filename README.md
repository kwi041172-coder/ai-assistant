# Vercel 배포 AI 비서

FastAPI, OpenAI API, Firestore로 동작하는 개인 데이터 기반 AI 비서입니다. Vercel의 Python 런타임에서 프런트엔드와 FastAPI를 같은 도메인으로 제공합니다.

> **공개 서비스 경고:** 앱 비밀번호 인증을 제거했습니다. 배포 URL을 아는 누구나 데이터와 대화 기록을 조회·추가·수정·삭제할 수 있고, OpenAI API 사용량을 발생시킬 수 있습니다. 비공개 개인 데이터를 저장하거나 무단 사용 비용을 감당할 수 없다면 공개 배포하지 마세요. 비밀번호 인증을 되살리거나 별도 인증 계층을 적용하기 전에는 실제 데이터를 넣지 않는 것을 권장합니다.

> **비용 안내:** Vercel과 Firebase의 무료 한도 안에서 사용할 수 있더라도 OpenAI API 호출은 별도로 과금될 수 있습니다. 모델 기본값은 `gpt-5-nano`입니다. Firebase Spark의 한도와 Vercel의 무료 플랜 제한은 제공자 정책에 따라 바뀔 수 있습니다.

## 로컬 실행

Python 3.10 이상이 필요합니다. 저장소 루트에서 `run.bat`을 실행하면 가상환경 생성, 백엔드 패키지 설치, 로컬 서버 실행을 진행합니다. 처음 실행 시 `backend/.env`가 없으면 예제 파일을 복사하고 종료하므로 OpenAI API 키를 입력한 뒤 다시 실행하세요. 브라우저에서 <http://127.0.0.1:8000>을 엽니다.

수동으로 실행하려면:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

`backend/.env`에 다음 변수를 설정합니다.

```dotenv
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-nano
FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-key.json
STORAGE_BACKEND=sqlite
SQLITE_DATABASE_PATH=local.sqlite3
```

`OPENAI_API_KEY`에는 OpenAI Platform에서 발급한 API 키를 사용해야 합니다. 다른 AI 서비스나 코딩 도우미의 키는 호환되지 않습니다. 키를 설정한 뒤 앱을 재시작하세요.

로컬에서는 SQLite가 `backend/local.sqlite3`에 데이터를 저장하므로 Firestore API를 켜지 않아도 데이터와 대화 기록 기능을 사용할 수 있습니다. 이 로컬 파일은 Git에 포함되지 않습니다. `OPENAI_API_KEY`와 Firebase 키는 프런트엔드 파일이나 저장소에 넣지 마세요.

## Vercel 배포

저장소 루트의 [pyproject.toml](./pyproject.toml)이 Vercel 공식 FastAPI 진입점 `backend.main:app`을 지정하고, [requirements.txt](./requirements.txt)가 백엔드 의존성을 불러옵니다. [vercel.json](./vercel.json)은 Vercel 기본 빌드 설정을 사용합니다. 프런트엔드는 FastAPI가 같은 도메인에서 제공하므로 별도 프런트엔드 배포나 `API_BASE_URL` 설정이 필요하지 않습니다.

1. GitHub 저장소 `kwi041172-coder/ai-assistant`의 `master` 브랜치를 Vercel에 Import하고 Root Directory를 저장소 루트로 둡니다.
2. Vercel 프로젝트 Settings → Environment Variables에서 다음 값을 설정합니다.
   - `OPENAI_API_KEY`: OpenAI Platform에서 발급한 유효한 API 키 (다른 서비스의 키는 사용할 수 없음)
   - `OPENAI_MODEL`: 선택 사항. 미설정 시 `gpt-5-nano`
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: Firebase 서비스 계정 JSON 전체 문자열
   - `STORAGE_BACKEND`: `firestore` (생략 시 기본값)
3. Environment에서 Production을 선택해 저장한 뒤 Deployments에서 재배포합니다.
4. Settings → Deployment Protection에서 Production 배포를 공개로 허용합니다. 이 설정이 켜져 있으면 앱 비밀번호를 제거해도 Vercel 로그인 화면이 먼저 표시됩니다. Preview 배포는 보호 상태로 둘 수 있습니다.
5. 배포 URL의 `/`, `/health`, `/docs`를 확인합니다.

`.env`, Firebase 서비스 계정 JSON, 가상환경은 Git에 올리지 마세요. Render 설정은 더 이상 사용하지 않습니다. 로컬 또는 Vercel 환경에 이전 앱 비밀번호 변수가 남아 있으면 삭제해도 됩니다. 현재 앱은 앱 비밀번호를 사용하지 않습니다.

프런트엔드만 별도 호스팅하는 경우에는 `frontend` 폴더에서 `npm run build`를 실행해 정적 파일을 만들 수 있습니다. 기본 빌드는 같은 출처의 API를 사용합니다. 백엔드가 다른 도메인에 있다면 빌드 전에 `API_BASE_URL`을 백엔드 출처(예: `https://api.example.com`)로 설정하고, 백엔드의 `ALLOWED_ORIGINS`에도 프런트엔드 출처를 추가하세요. 브라우저에 OpenAI 또는 Firebase 비밀 키를 설정하지 마세요.

합성 데모 데이터를 넣으려면 Firebase 설정 후 저장소 루트에서 `python -m backend.seed_sample_data`를 실행합니다. 스크립트는 날짜별 고정 문서 ID를 사용하므로 중복 실행 시 이미 있는 문서는 건너뜁니다.

### Firestore 설정 및 장애 동작

Firebase 프로젝트에서 Cloud Firestore API를 활성화하고 Firestore 데이터베이스를 생성해야 데이터를 추가·조회하고 대화 기록을 저장할 수 있습니다. API가 비활성화된 경우 데이터 API는 `503`과 설정 안내를 반환합니다. 채팅은 개인 데이터 없이 계속 응답하지만, 요약과 대화 저장은 사용할 수 없습니다. Vercel의 `FIREBASE_SERVICE_ACCOUNT_JSON`은 해당 Firebase 프로젝트의 서비스 계정 JSON이어야 합니다.

## API

| Method | 경로 | 설명 |
| --- | --- | --- |
| `POST` | `/api/chat` | OpenAI 응답 생성 |
| `GET`, `POST` | `/api/data` | 데이터 목록 및 추가 |
| `PUT`, `DELETE` | `/api/data/{id}` | 데이터 수정 및 삭제 |
| `GET` | `/api/data/summary` | 개인 데이터 통계 요약 |
| `GET`, `POST` | `/api/conversations` | 대화 목록 및 저장 |
| `GET`, `PUT`, `DELETE` | `/api/conversations/{id}` | 대화 조회, 갱신, 삭제 |
| `DELETE` | `/api/conversations` | 모든 대화 삭제 |
| `GET` | `/health` | 백엔드 상태 확인 |

API 문서는 `/docs`에서 확인할 수 있습니다.
