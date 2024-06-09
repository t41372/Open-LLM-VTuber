from fastapi import FastAPI, WebSocket, APIRouter, Body
from starlette.websockets import WebSocketDisconnect
from typing import List

app = FastAPI()
router = APIRouter()

# 存儲已連接的WebSocket客戶端
connected_clients: List[WebSocket] = []

@router.websocket("/live2d-motion-ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # 保持連接開啟，直到客戶端斷開連接
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@router.post("/broadcast")
async def broadcast_message(message: str = Body(..., embed=True)):
    disconnected_clients = []
    for client in connected_clients:
        try:
            await client.send_text(message)
        except WebSocketDisconnect:
            disconnected_clients.append(client)
    for client in disconnected_clients:
        connected_clients.remove(client)

app.include_router(router)

# 如果直接運行此文件，則啟動伺服器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)