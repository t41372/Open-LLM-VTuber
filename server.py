from fastapi import FastAPI, WebSocket, APIRouter, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from typing import List, Dict

import yaml


class WebSocketServer:
    """
    WebSocketServer initializes a FastAPI application with WebSocket endpoints and a broadcast endpoint.

    Attributes:
        config (dict): Configuration dictionary.
        app (FastAPI): FastAPI application instance.
        router (APIRouter): APIRouter instance for routing.
        connected_clients (List[WebSocket]): List of connected WebSocket clients for "/client-ws".
        server_ws_clients (List[WebSocket]): List of connected WebSocket clients for "/server-ws".
    """

    def __init__(self):
        """
        Initializes the WebSocketServer with the given configuration.
        """
        self.app = FastAPI()
        self.router = APIRouter()
        self.connected_clients: List[WebSocket] = []
        self.server_ws_clients: List[WebSocket] = []
        self._setup_routes()
        self._mount_static_files()

    def _setup_routes(self):
        """Sets up the WebSocket and broadcast routes."""

        @self.router.websocket("/server-ws")
        async def server_websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.server_ws_clients.append(websocket)
            # When a connection is established, send a specific payload to all clients connected to "/client-ws"
            control_message = {"type": "control", "text": "start-mic"}
            for client in self.connected_clients:
                await client.send_json(control_message)
            try:
                while True:
                    # Receive messages from "/server-ws" clients
                    message = await websocket.receive_text()
                    # Forward received messages to all clients connected to "/client-ws"
                    for client in self.connected_clients:
                        await client.send_text(message)
            except WebSocketDisconnect:
                self.server_ws_clients.remove(websocket)

        @self.router.websocket("/client-ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            try:
                while True:
                    # Receive messages from "/client-ws" clients
                    message = await websocket.receive_text()
                    # Forward received messages to all clients connected to "/server-ws"
                    for server_client in self.server_ws_clients:
                        await server_client.send_text(message)
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)

        @self.router.post("/broadcast")
        async def broadcast_message(message: str = Body(..., embed=True)):
            disconnected_clients = []
            for client in self.connected_clients:
                try:
                    await client.send_text(message)
                except WebSocketDisconnect:
                    disconnected_clients.append(client)
            for client in disconnected_clients:
                self.connected_clients.remove(client)

        self.app.include_router(self.router)

    def _mount_static_files(self):
        """Mounts static file directories."""
        self.app.mount(
            "/live2d-models",
            StaticFiles(directory="live2d-models"),
            name="live2d-models",
        )
        self.app.mount("/", StaticFiles(directory="./static", html=True), name="static")

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Runs the FastAPI application using Uvicorn."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    # Load configurations from yaml file
    with open("conf.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Initialize and run the WebSocket server
    server = WebSocketServer()
    server.run(host=config["host"], port=config["port"])
