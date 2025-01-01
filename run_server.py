import atexit
import tomli
import uvicorn
from loguru import logger
import sys
from src.open_llm_vtuber.server import WebSocketServer
from src.open_llm_vtuber.config_manager import Config, read_yaml, validate_config


@logger.catch
def run():
    logger.info(f"t41372/Open-LLM-VTuber, version v{get_version()}")

    atexit.register(WebSocketServer.clean_cache)

    # Load configurations from yaml file
    config: Config = validate_config(read_yaml("conf.yaml"))
    server_config = config.system_config
    # config["LIVE2D"] = True  # make sure the live2d is enabled

    # Initialize and run the WebSocket server
    server = WebSocketServer(config=config)
    uvicorn.run(
        app=server.app,
        host=server_config.host,
        port=server_config.port,
        log_level="debug",
    )


def get_version():
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)
    return pyproject["project"]["version"]


def init_logger(console_log_level="INFO"):
    logger.remove()
    # Console output
    logger.add(
        sys.stderr,
        level=console_log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
        colorize=True,
    )

    # File output
    logger.add(
        "logs/debug_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}",
        backtrace=True,
        diagnose=True,
    )


if __name__ == "__main__":
    init_logger(console_log_level="DEBUG")
    run()
