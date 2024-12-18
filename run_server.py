import atexit
import tomli
import uvicorn
from loguru import logger
from src.open_llm_vtuber.server import WebSocketServer
from open_llm_vtuber.utils.config_loader import load_config


@logger.catch
def run():
    logger.info(
        f"t41372/Open-LLM-VTuber, version v{get_version()}"
    )

    atexit.register(WebSocketServer.clean_cache)

    # Load configurations from yaml file
    config = load_config("conf.yaml")
    server_config = config["SYSTEM_CONFIG"]
    # config["LIVE2D"] = True  # make sure the live2d is enabled

    # Initialize and run the WebSocket server
    server = WebSocketServer(config=config)
    uvicorn.run(
        app=server.app,
        host=server_config["HOST"],
        port=server_config["PORT"],
        log_level="debug",
    )

def get_version():
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)
    return pyproject["project"]["version"]


if __name__ == "__main__":
    run()
