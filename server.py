from fastapi import FastAPI, WebSocket, APIRouter, Body
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from typing import List

import yaml
# Load configurations
def load_config():
    with open('conf.yaml', 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Simplified configuration access
def get_config(key, default=None):
    return config.get(key, default)


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

app.mount("/", StaticFiles(directory="./static", html=True), name="static")

# 如果直接運行此文件，則啟動伺服器
if __name__ == "__main__":
    import uvicorn
    host = get_config("HOST", default="127.0.0.1")
    port = get_config("PORT", default=8000)
    uvicorn.run(app, host=host, port=port)