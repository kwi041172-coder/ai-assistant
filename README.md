# Vercel 배포 AI 비서

FastAPI, OpenAI API, Firestore로 동작하는 개인 데이터 기반 AI 비서입니다. Vercel의 Python 런타임에서 프런트엔드와 FastAPI를 같은 도메인으로 제공합니다.

> **공개 서비스 경고:** 앱 비밀번호 인증을 제거했습니다. 배포 URL을 아는 누구나 데이터와 대화 기록을 조회·추가·수정·삭제할 수 있고, OpenAI API 사용량을 발생시킬 수 있습니다. 비공개 개인 데이터를 저장하거나 무단 사용 비용을 감당할 수 없다면 공개 배포하지 마세요. 비밀번호 인증을 되살리거나 별도 인증 계층을 적용하기 전에는 실제 데이터를 넣지 않는 것을 권장합니다.

> **비용 안내:** Vercel과 Firebase의 무료 한도 안에서 사용할 수 있더라도 OpenAI API 호출은 별도로 과금될 수 있습니다. 모델 기본값은 `gpt-5-nano`입니다. Firebase Spark의 한도와 Vercel의 무료 플랜 제한은 제공자 정책에 따라 바뀔 수 있습니다.

## 로컬 실행

Python 3.10 이상이 필요합니다. 기존 `backend/.env`의 `OPENAI_API_KEY`는 유지하세요. 비밀번호 환경변수는 더 이상 필요하지 않습니다.

PowerShell에서:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

`backend/.env`에 다음 변수를 설정합니다.

```dotenv
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-nano
FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-key.json
```

Firebase 서비스 계정 키는 `backend/firebase-key.json`에 두며 Git에 추가하지 마세요. `OPENAI_API_KEY`와 Firebase 키는 프런트엔드 파일이나 저장소에 넣지 마세요. 브라우저에서 <http://127.0.0.1:8000>을 엽니다.

## Vercel 배포

저장소 루트에 Vercel용 FastAPI 진입점인 [app.py](./app.py)와 루트 의존성 파일 [requirements.txt](./requirements.txt)가 있습니다. [vercel.json](./vercel.json)은 Vercel 기본 빌드 설정을 사용합니다.

1. GitHub 저장소 `kwi041172-coder/ai-assistant`의 `master` 브랜치를 Vercel에 Import하고 Root Directory를 저장소 루트로 둡니다.
2. Vercel 프로젝트 Settings → Environment Variables에서 다음 값을 설정합니다.
   - `OPENAI_API_KEY`: 기존 OpenAI API 키
   - `OPENAI_MODEL`: 선택 사항. 미설정 시 `gpt-5-nano`
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: Firebase 서비스 계정 JSON 전체 문자열
3. Environment에서 Production을 선택해 저장한 뒤 Deployments에서 재배포합니다.
4. Settings → Deployment Protection에서 Production 배포를 공개로 허용합니다. 이 설정이 켜져 있으면 앱 비밀번호를 제거해도 Vercel 로그인 화면이 먼저 표시됩니다. Preview 배포는 보호 상태로 둘 수 있습니다.
5. 배포 URL의 `/`, `/health`, `/docs`를 확인합니다.

`.env`, Firebase 서비스 계정 JSON, 가상환경은 Git에 올리지 마세요. Render 설정은 더 이상 사용하지 않습니다. 로컬 또는 Vercel 환경에 이전 앱 비밀번호 변수가 남아 있으면 삭제해도 됩니다. 현재 앱은 앱 비밀번호를 사용하지 않습니다.

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
