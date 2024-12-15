import atexit
import os
import shutil
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn

from .config.config_manager import load_config_with_env
from .service.model_manager import ModelManager
from .service.service_context import ServiceContext
from .routes import create_routes

class WebSocketServer:
    @staticmethod
    def clean_cache():
        """Clean the cache directory by removing and recreating it."""
        cache_dir = "./cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)

    def __init__(self, open_llm_vtuber_main_config):
        self.config = open_llm_vtuber_main_config
        
        # Initialize model manager and service context
        self.model_manager = ModelManager(self.config)
        self.service_context = ServiceContext(self.config, self.model_manager)

        self.app = FastAPI()

        # Add CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include routes
        self.app.include_router(create_routes(self.service_context))
        
        # Mount static files
        self.app.mount("/live2d-models", StaticFiles(directory="live2d-models"), name="live2d-models")
        self.app.mount("/", StaticFiles(directory="./static", html=True), name="static")

        logger.info(f"t41372/Open-LLM-VTuber, version {self.config.get('__version__','unknown')}")

    def run(self, host, port):
        uvicorn.run(self.app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    atexit.register(WebSocketServer.clean_cache)

    # Load configurations
    config = load_config_with_env("conf.yaml")
    config["LIVE2D"] = True  # ensure live2d is enabled

    server = WebSocketServer(config)
    server.run(host=config["HOST"], port=config["PORT"])
