from fastapi import FastAPI, WebSocket, APIRouter, Body
from fastapi.responses import FileResponse
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

server_ws_clients = []

@router.websocket("/server-ws")
async def server_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    server_ws_clients.append(websocket)
    # 當與客戶端建立連接時，向所有連接到 "/client-ws" 的客戶端發送特定的 payload
    control_message = {"type": "control", "text": "start-mic"}
    for client in connected_clients:  # 假設 connected_clients 是連接到 "/client-ws" 的客戶端列表
        await client.send_json(control_message)
    try:
        while True:
            # 接收來自 "/server-ws" 客戶端的消息
            message = await websocket.receive_text()
            # 將接收到的消息轉發給所有連接到 "/client-ws" 的客戶端
            for client in connected_clients:
                await client.send_text(message)
    except WebSocketDisconnect:
        server_ws_clients.remove(websocket)

# 修改原有的 websocket_endpoint 函數，使其能夠接收消息並轉發給 "/server-ws" 的客戶端
@router.websocket("/client-ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # 接收來自 "/client-ws" 客戶端的消息
            message = await websocket.receive_text()
            # 將接收到的消息轉發給所有連接到 "/server-ws" 的客戶端
            for server_client in server_ws_clients:
                await server_client.send_text(message)
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

app.mount("/live2d-models", StaticFiles(directory="live2d-models"), name="live2d-models")
app.mount("/", StaticFiles(directory="./static", html=True), name="static")

# 如果直接運行此文件，則啟動伺服器
if __name__ == "__main__":
    import uvicorn
    host = get_config("HOST", default="127.0.0.1")
    port = get_config("PORT", default=8000)
    uvicorn.run(app, host=host, port=port)