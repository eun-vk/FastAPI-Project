import os
import uuid
from datetime import datetime
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Query, Cookie, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette import status

from models import UserCreate, UserLogin, UserResponse
from auth import create_user, authenticate_user, create_session, get_current_user, logout_user, users_db


# --- 환경 변수 로드 ---
load_dotenv()
API_KEY = os.getenv("GPT_API_KEY")
if not API_KEY:
    raise RuntimeError("환경변수 GPT_API_KEY가 설정되어 있지 않습니다.")


# --- FastAPI 앱 및 설정 ---
app = FastAPI()

# CORS 설정
origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- 인메모리 DB 구조 ---
# {user_id: [{"id": str, "question": str, "answer": str, "timestamp": str, "session_id": str}]}
messages_db = {}
# {user_id: current_session_id}
active_sessions = {}


GPT_PROXY_URL = "https://dev.wenivops.co.kr/services/openai-api"


# --- Pydantic 모델 ---
class ChatRequest(BaseModel):
    user_id: str
    question: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    message_id: str
    session_id: str
    timestamp: str


class ChatMessage(BaseModel):
    id: str
    question: str
    answer: str
    timestamp: str
    session_id: str


class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    created_at: str
    last_message_at: str


# --- 유틸리티 함수 ---
def get_current_timestamp() -> str:
    """현재 UTC 타임스탬프를 ISO 형식으로 반환합니다."""
    return datetime.now().isoformat()


def generate_session_id() -> str:
    """고유한 세션 ID를 생성합니다."""
    return str(uuid.uuid4())


def generate_message_id() -> str:
    """고유한 메시지 ID를 생성합니다."""
    return str(uuid.uuid4())


def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> str:
    """
    주어진 사용자에 대해 기존 세션 ID를 검색하거나 새 세션을 생성합니다.
    session_id가 제공되면 해당 ID를 직접 사용합니다. 그렇지 않으면 새 세션을 생성합니다.
    """
    if session_id:
        return session_id
    new_session_id = generate_session_id()
    active_sessions[user_id] = new_session_id
    return new_session_id


# --- GPT 프록시 호출 함수 ---
async def call_gpt_proxy(messages: list) -> str:
    """
    메시지 목록으로 GPT 프록시 서비스를 호출하고 AI의 응답을 반환합니다.
    잠재적인 요청 및 HTTP 상태 오류를 처리합니다.
    """
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(GPT_PROXY_URL, json=messages, headers=headers)
            response.raise_for_status()  # 잘못된 상태 코드에 대해 예외 발생
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return data.get("answer", "응답이 없습니다.")
    except httpx.RequestError as e:
        return f"요청 실패: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP 에러: {e.response.status_code}"


# --- 웹 페이지 라우터 (HTML 응답) ---

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """메인 홈페이지를 제공합니다."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지를 제공합니다."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """사용자 로그인 시도를 처리하고 성공 시 세션 쿠키를 설정합니다."""
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "사용자명 또는 비밀번호가 올바르지 않습니다."
        })

    session_id = create_session(username)
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie("session_id", session_id, httponly=True, max_age=3600)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """회원가입 페이지를 제공합니다."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def handle_register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    """사용자 회원가입 시도를 처리합니다."""
    result = create_user(username=username, email=email, password=password)
    if not result["success"]:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": result["message"]
        })

    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response


# --- API 엔드포인트: 사용자 관리 (JSON 응답) ---

@app.post("/api/register")
async def api_register(user_data: UserCreate):
    """API를 통해 새 사용자를 등록합니다."""
    result = create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    user_response = UserResponse(
        id=result["user"].id,
        username=result["user"].username,
        email=result["user"].email
    )
    return {
        "message": "회원가입이 완료되었습니다!",
        "user": user_response
    }


@app.post("/api/login")
async def api_login(user_data: UserLogin):
    """API를 통해 사용자를 로그인시키고 세션 쿠키를 설정합니다."""
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail=" 사용자명 또는 비밀번호가 올바르지 않습니다")

    session_id = create_session(user_data.username)
    response = JSONResponse({
        "message": "로그인 성공!",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=3600
    )
    return response


@app.get("/api/me", response_model=UserResponse)
async def api_get_me(session_id: Optional[str] = Cookie(None)):
    """세션 ID를 기반으로 현재 사용자 정보를 검색합니다."""
    if not session_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")

    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다. 다시 로그인해주세요")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email
    )


@app.post("/api/logout")
async def api_logout(session_id: Optional[str] = Cookie(None)):
    """세션을 무효화하여 현재 사용자를 로그아웃합니다."""
    if session_id:
        logout_user(session_id)

    response = JSONResponse({"message": "👋 로그아웃되었습니다"})
    response.delete_cookie("session_id")
    return response


@app.get("/api/users")
async def api_get_all_users():
    """모든 등록된 사용자 목록을 검색합니다 (디버깅/관리 목적)."""
    return {
        "총_사용자_수": len(users_db),
        "사용자_목록": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            for user in users_db.values()
        ]
    }


# --- API 엔드포인트: 채팅 기능 ---
@app.get("/journals-page", response_class=HTMLResponse) # 채팅 기록(journals.html) 페이지를 제공합니다.
async def journals_page(request: Request):
    """채팅 기록(journals.html) 페이지를 제공합니다."""
    return templates.TemplateResponse("journals.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_req: ChatRequest):
    """
    채팅 요청을 처리하고, GPT 프록시로 질문을 보내고, 대화를 저장하며, AI의 응답을 반환합니다.
    """
    user_id = chat_req.user_id
    question = chat_req.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    session_id = get_or_create_session(user_id, chat_req.session_id)

    # 시스템 지침으로 메시지 초기화
    messages = [{"role": "system", "content": "You are a helpful assistant for social welfare counseling."}]

    # 컨텍스트를 위해 최근 메시지 가져와 추가
    if user_id in messages_db:
        session_messages = [msg for msg in messages_db[user_id] if msg["session_id"] == session_id]
        # 컨텍스트를 위해 마지막 5개 메시지까지 추가
        for msg in session_messages[-5:]:
            messages.append({"role": "user", "content": msg["question"]})
            messages.append({"role": "assistant", "content": msg["answer"]})

    messages.append({"role": "user", "content": question})
    ai_answer = await call_gpt_proxy(messages)

    message_id = generate_message_id()
    timestamp = get_current_timestamp()

    new_message = {
        "id": message_id,
        "question": question,
        "answer": ai_answer,
        "timestamp": timestamp,
        "session_id": session_id
    }

    if user_id not in messages_db:
        messages_db[user_id] = []

    messages_db[user_id].append(new_message)

    return ChatResponse(
        answer=ai_answer,
        message_id=message_id,
        session_id=session_id,
        timestamp=timestamp
    )


@app.get("/chat/sessions", response_model=List[ChatSession])
async def get_chat_sessions(user_id: str = Query(...)):
    """주어진 사용자의 모든 채팅 세션 목록을 검색합니다."""
    if user_id not in messages_db:
        return []

    user_messages = messages_db[user_id]
    sessions_dict = {}
    for msg in user_messages:
        session_id = msg["session_id"]
        if session_id not in sessions_dict:
            sessions_dict[session_id] = []
        sessions_dict[session_id].append(msg)

    sessions = []
    for session_id, messages in sessions_dict.items():
        messages.sort(key=lambda x: x["timestamp"])  # 세션 내 메시지를 타임스탬프별로 정렬
        chat_messages = [ChatMessage(**msg) for msg in messages]
        sessions.append(ChatSession(
            session_id=session_id,
            messages=chat_messages,
            created_at=messages[0]["timestamp"],
            last_message_at=messages[-1]["timestamp"]
        ))

    sessions.sort(key=lambda x: x.last_message_at, reverse=True)  # 마지막 메시지 시간으로 세션 정렬
    return sessions


@app.get("/chat/session/{session_id}", response_model=ChatSession)
async def get_chat_session_by_id(session_id: str, user_id: str = Query(...)):
    """주어진 사용자의 ID로 특정 채팅 세션을 검색합니다."""
    if user_id not in messages_db:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    session_messages = [msg for msg in messages_db[user_id] if msg["session_id"] == session_id]
    if not session_messages:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    session_messages.sort(key=lambda x: x["timestamp"])
    chat_messages = [ChatMessage(**msg) for msg in session_messages]

    return ChatSession(
        session_id=session_id,
        messages=chat_messages,
        created_at=session_messages[0]["timestamp"],
        last_message_at=session_messages[-1]["timestamp"]
    )


@app.post("/chat/new-session")
async def create_new_session(user_id: str = Query(...)):
    """사용자를 위한 새 채팅 세션을 생성합니다."""
    new_session_id = generate_session_id()
    active_sessions[user_id] = new_session_id
    return {
        "session_id": new_session_id,
        "message": "새로운 세션이 생성되었습니다."
    }


@app.get("/user/{user_id}/current-session")
async def get_current_session_for_user(user_id: str):
    """사용자의 현재 활성 채팅 세션 ID를 검색하며, 없으면 생성합니다."""
    current_session = active_sessions.get(user_id)
    if not current_session:
        current_session = generate_session_id()
        active_sessions[user_id] = current_session
    return {"session_id": current_session}

# 여기는 주석으로 처리되어 있어야 할 부분이 코드에 포함되어 있었습니다.
# 이 부분은 주석으로 남기거나, 해당 라우트가 필요하다면 별도의 고유한 경로를 지정해야 합니다.
# 현재 이 부분은 주석으로 표시된 설명만 있고 실제 라우트 데코레이터가 없습니다.
# (사용되지 않는 주석이므로 제거할 수 있습니다.)

@app.delete("/chat/message/{message_id}")
async def delete_chat_message(message_id: str, user_id: str = Query(...)):
    """주어진 사용자에 대해 ID로 특정 채팅 메시지를 삭제합니다."""
    if user_id not in messages_db:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    original_len = len(messages_db[user_id])
    messages_db[user_id] = [
        msg for msg in messages_db[user_id] if msg["id"] != message_id
    ]

    if len(messages_db[user_id]) == original_len:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    return {"message": "메시지가 삭제되었습니다.", "message_id": message_id}


# --- 개발자 디버그 엔드포인트 ---

@app.get("/debug/db")
async def debug_db():
    """인메모리 데이터베이스의 현재 상태를 볼 수 있는 엔드포인트를 제공합니다."""
    return {
        "messages_db": messages_db,
        "active_sessions": active_sessions
    }


# --- 서버 실행 ---

if __name__ == "__main__":
    import uvicorn
    print("서버를 시작합니다...")
    print("http://localhost:8000 접속")
    print("API 문서는 http://localhost:8000/docs 에서 확인하세요")
    uvicorn.run(app, host="0.0.0.0", port=8000)