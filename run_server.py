import atexit
import uvicorn
from fastapi import FastAPI
from src.open_llm_vtuber.server import WebSocketServer
from src.open_llm_vtuber.utils.utils import load_config_with_env


if __name__ == "__main__":

    atexit.register(WebSocketServer.clean_cache)

    # Load configurations from yaml file
    config = load_config_with_env("conf.yaml")

    config["LIVE2D"] = True  # make sure the live2d is enabled

    # Initialize and run the WebSocket server
    server = WebSocketServer(open_llm_vtuber_main_config=config)
    uvicorn.run(app=server.app, host=config["HOST"], port=config["PORT"], log_level="info")
    