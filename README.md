# 무료 구간으로 배포하는 AI 비서

FastAPI, OpenAI API, Firestore로 동작하는 개인 데이터 기반 채팅 앱입니다. 프론트엔드와 백엔드는 Render 무료 서비스, 데이터베이스는 Firebase Spark(무료) 플랜으로 배포하도록 구성했습니다.

> **중요한 비용 안내:** Render와 Firestore를 무료 한도 안에서 쓸 수 있어도, `OPENAI_API_KEY`는 OpenAI 공식 API 키이므로 AI 응답마다 OpenAI API 사용료가 발생할 수 있습니다. 따라서 이 앱 전체의 비용이 항상 0원이라고 보장할 수는 없습니다. 모델 기본값은 비용을 줄이기 위해 `gpt-5-nano`로 설정했으며, 현재 요금과 사용량은 [OpenAI API 가격](https://openai.com/api/pricing/) 및 사용량 대시보드에서 확인하세요. 완전한 0원 운영이 필수라면 OpenAI API 호출을 끄고 별도 로컬 모델을 사용해야 합니다.

## 무료 배포 구성

| 구성 | 선택 | 무료 사용 시 유의사항 |
| --- | --- | --- |
| 웹 앱 + FastAPI 백엔드 | Render Free Web Service 한 개 | 15분 유휴 후 sleep, 다음 요청에 약 1분 기동 대기. 워크스페이스당 월 무료 인스턴스 시간 750시간 및 네트워크 한도 적용 |
| 데이터베이스 | Cloud Firestore Spark | 기본 무료 데이터베이스 1개 기준 저장 1GiB, 읽기 50,000건/일, 쓰기·삭제 각 20,000건/일 등 할당량 적용 |
| AI 모델 | OpenAI API (`gpt-5-nano`) | 무료 호스팅과 별개로 API 사용료가 발생할 수 있음 |

요금이 청구되는 것을 막으려면 Firebase 프로젝트를 **Spark에 유지**하고 Google Cloud 결제를 연결하지 마세요. Render에서도 Free 이외의 인스턴스로 변경하거나 결제수단/유료 업그레이드를 설정하지 마세요. Render는 무료 백엔드를 15분 유휴 뒤 잠재우며, 월 제공량에 도달하면 정지될 수 있습니다. 결제수단을 등록하지 않으면 초과 사용 시 과금 대신 서비스가 일시 중단되도록 관리할 수 있습니다. 무료 제공량을 넘기면 Firestore 요청이 제한되거나 호스팅이 멈출 수 있으나 유료 플랜으로 자동 전환하지 않도록 하세요. 각 제공자의 무료 정책과 한도는 변경될 수 있으니 배포 전에 공식 요금 페이지에서 확인하세요.

- [Firebase 요금 및 Spark 무료 할당량](https://firebase.google.com/pricing)
- [Render 무료 서비스 제한](https://render.com/docs/free)
- [OpenAI API 가격](https://openai.com/api/pricing/)

## 로컬 실행

Python 3.10 이상을 사용합니다. 기존 `backend/.env`의 `OPENAI_API_KEY`는 그대로 유지하세요. 서비스 계정 JSON을 `.env`에 여러 줄로 직접 붙여 넣으면 dotenv가 읽지 못하므로, 로컬 Firebase 키는 `backend/firebase-key.json` 파일로 저장하고 `.env`에는 파일 경로를 지정합니다.

PowerShell에서:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`backend/.env`에 필요한 설정:

```dotenv
OPENAI_API_KEY=기존_키_그대로_유지
OPENAI_MODEL=gpt-5-nano
APP_ACCESS_PASSWORD=길고_무작위인_비밀번호
FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-key.json
```

`OPENAI_API_KEY` 값은 프론트엔드 파일이나 Git 저장소에 넣지 마세요. 현재 로컬 `.env`에 여러 줄 JSON으로 저장되어 있던 Firebase 서비스 계정 키는 `backend/firebase-key.json`으로 옮겼으며, `.env`의 경로를 설정했습니다. 이 키 파일은 `.gitignore`로 제외됩니다. Firebase Admin 키는 발급 자체는 무료지만 권한이 강한 비밀 자격증명입니다.

`APP_ACCESS_PASSWORD`는 개인 앱 API와 Firestore 데이터에 대한 접근을 보호합니다. 로컬 `.env`에는 새 임의 비밀번호를 만들었습니다. 앱 로그인 화면에서 이 값을 사용하세요. 배포 시에는 별도의 강한 비밀번호를 Render 환경변수에 등록합니다. 브라우저에는 비밀번호가 탭이 열린 동안에만 보관됩니다.

백엔드:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

위 명령은 첫 설정에서 이동한 `backend` 폴더에서 실행합니다.

브라우저에서 <http://127.0.0.1:8000>을 엽니다. FastAPI가 UI와 API를 같은 origin으로 제공하므로 별도 프론트엔드 서버나 CORS 설정은 필요하지 않습니다. API 주소는 [config.js](./frontend/config.js)에서 상대 경로 `/api`로 설정되어 있습니다.

## Render 무료 배포

저장소에는 UI와 백엔드를 한 개의 무료 웹 서비스로 배포하는 [render.yaml](./render.yaml)이 있습니다. Render Blueprint는 Git 저장소에서 가져오므로, 저장소를 GitHub 등 Git 제공자에 올려 Render 계정에 연결해야 합니다. `.env`, Firebase 키 JSON, 가상환경 폴더는 커밋하지 마세요.

1. Firebase Console에서 프로젝트를 만들고 **Cloud Firestore (Native mode)** 데이터베이스를 생성합니다. Spark 무료 플랜을 유지하고 결제를 연결하지 않습니다.
2. Firebase 서비스 계정 키 JSON을 생성합니다. JSON 내용은 비밀이므로 저장소에 절대 추가하지 않습니다.
3. Render에서 **New > Blueprint**를 선택해 저장소와 `render.yaml`을 연결하고, 무료 플랜으로 `ai-assistant-api` 서비스를 배포합니다. 기존에 같은 이름의 API 서비스가 있으면 해당 서비스 설정을 갱신합니다.
4. Render의 서비스 **Environment** 화면에서 다음 변수를 설정합니다.
   - `OPENAI_API_KEY`: 기존 OpenAI API 키
   - `APP_ACCESS_PASSWORD`: 앱 사용자가 로그인할 강력한 임의 비밀번호
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: Firebase 서비스 계정 JSON 전체 내용 또는 서비스의 Secret File 경로
   - `OPENAI_MODEL`: 기본값 `gpt-5-nano` (Blueprint 기본값 사용 가능)
5. Firebase JSON을 `FIREBASE_SERVICE_ACCOUNT_JSON` 변수에 넣고 싶지 않다면 **Secret Files**에 `firebase-key.json`으로 추가하고, 환경변수에는 `/etc/secrets/firebase-key.json`을 넣습니다.
6. 배포 로그가 성공하면 서비스 주소를 엽니다. UI는 `/`, 상태 확인은 `/health`, API 문서는 `/docs`입니다.

Blueprint에서 정의한 `OPENAI_API_KEY`, `APP_ACCESS_PASSWORD`, `FIREBASE_SERVICE_ACCOUNT_JSON`은 비밀 값이라 Render 대시보드에서 입력해야 합니다. 비밀 키를 Blueprint 파일이나 Git에 쓰지 마세요. Firebase 서비스는 JSON 문자열과 파일 경로 두 방식 모두 지원합니다. Render 무료 백엔드는 유휴 상태에서 잠들 수 있어 처음 방문은 늦을 수 있습니다. 앱 데이터는 일시적인 웹서버 파일시스템이 아닌 Firestore에 저장됩니다.

## API 요약

| Method | 경로 | 설명 |
| --- | --- | --- |
| `POST` | `/api/chat` | OpenAI 응답 생성 |
| `GET`, `POST` | `/api/data` | 데이터 목록 및 추가 |
| `PUT`, `DELETE` | `/api/data/{id}` | 데이터 수정 및 삭제 |
| `GET` | `/api/data/summary` | 개인 데이터 통계 요약 |
| `GET`, `POST` | `/api/conversations` | 대화 목록 및 저장 |
| `GET`, `PUT`, `DELETE` | `/api/conversations/{id}` | 대화 조회, 갱신, 삭제 |
| `DELETE` | `/api/conversations` | 모든 대화 삭제 |
| `GET` | `/api/auth/check` | 앱 접속 비밀번호 확인 |
| `GET` | `/health` | 백엔드 상태 확인 |

API 문서는 백엔드 실행 후 `/docs`에서 확인할 수 있습니다.
