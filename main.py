# main.py (수정)

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------
# ✨ 새로운 부분: 연결 관리자 클래스
# --------------------------------------------------
class ConnectionManager:
    def __init__(self):
        # 활성화된 연결(WebSocket 객체)을 저장할 리스트
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # 새로운 클라이언트의 연결을 수락하고 목록에 추가
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # 클라이언트와의 연결을 끊고 목록에서 제거
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # 연결된 모든 클라이언트에게 메시지를 전송
        for connection in self.active_connections:
            await connection.send_text(message)

# 연결 관리자 인스턴스 생성
manager = ConnectionManager()
# --------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 웹소켓 경로 수정
@app.websocket("/ws/{client_id}") # 👈 경로에 client_id 추가
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # 새로운 클라이언트 연결
    await manager.connect(websocket)
    # 새로운 클라이언트 입장을 모든 사람에게 알림
    await manager.broadcast(f"📢 '{client_id}' 님이 입장했습니다.")
    
    try:
        # 클라이언트로부터 메시지를 계속 기다림
        while True:
            data = await websocket.receive_text()
            # 받은 메시지를 보낸 사람 정보와 함께 모든 사람에게 전달
            await manager.broadcast(f"[{client_id}]: {data}")
    except WebSocketDisconnect:
        # 클라이언트 연결이 끊어지면
        manager.disconnect(websocket)
        # 클라이언트 퇴장을 모든 사람에게 알림
        await manager.broadcast(f"📢 '{client_id}' 님이 퇴장했습니다.")