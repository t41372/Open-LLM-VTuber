import os
import re
import shutil
import atexit
import json
import asyncio
from typing import List, Dict, Any
import yaml
import numpy as np
from fastapi import FastAPI, WebSocket, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from main import OpenLLMVTuberMain
from live2d_model import Live2dModel
from tts.stream_audio import AudioPayloadPreparer
import chardet
from loguru import logger


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

    def __init__(self, open_llm_vtuber_main_config: Dict | None = None):
        """
        Initializes the WebSocketServer with the given configuration.
        """
        self.app = FastAPI()
        self.router = APIRouter()
        self.connected_clients: List[WebSocket] = []
        self.open_llm_vtuber_main_config = open_llm_vtuber_main_config
        
        # Initialize model manager
        self.preload_models = self.open_llm_vtuber_main_config.get("SERVER", {}).get("PRELOAD_MODELS", False)
        if self.preload_models:
            logger.info("Preloading ASR and TTS models...")
            logger.info("Using: " + str(self.open_llm_vtuber_main_config.get("ASR_MODEL")))
            logger.info("Using: " + str(self.open_llm_vtuber_main_config.get("TTS_MODEL")))
            
            self.model_manager = ModelManager(self.open_llm_vtuber_main_config)
            self.model_manager.initialize_models()
        
        self._setup_routes()
        self._mount_static_files()
        self.app.include_router(self.router)

    async def _handle_config_switch(self, websocket: WebSocket, config_file: str) -> tuple[Live2dModel, OpenLLMVTuberMain] | None:
        """处理配置切换，返回新的组件实例"""
        new_config = self._load_config_from_file(config_file)
        if new_config:
            try:
                # 更新模型缓存
                if self.preload_models:
                    self.model_manager.update_models(new_config)
                
                # 更新当前配置
                self.open_llm_vtuber_main_config.update(new_config)

                # 重新初始化组件
                l2d, open_llm_vtuber, _ = self._initialize_components(websocket)

                await websocket.send_text(
                    json.dumps({
                        "type": "config-switched",
                        "message": f"Switched to config: {config_file}",
                    })
                )
                await websocket.send_text(
                    json.dumps({"type": "set-model", "text": l2d.model_info})
                )
                logger.info(f"Configuration switched to {config_file}")
                
                return l2d, open_llm_vtuber
                
            except Exception as e:
                logger.error(f"Error switching configuration: {e}")
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": f"Error switching configuration: {str(e)}",
                    })
                )
                return None
        return None

    def _initialize_components(
        self, websocket: WebSocket
    ) -> tuple[Live2dModel, OpenLLMVTuberMain, AudioPayloadPreparer]:
        """Initialize or reinitialize components with current configuration."""
        l2d = Live2dModel(self.open_llm_vtuber_main_config["LIVE2D_MODEL"])
        
        # Use cached models if available
        custom_asr = self.model_manager.cache.get('asr') if self.preload_models else None
        custom_tts = self.model_manager.cache.get('tts') if self.preload_models else None
        
        open_llm_vtuber = OpenLLMVTuberMain(
            self.open_llm_vtuber_main_config,
            custom_asr=custom_asr,
            custom_tts=custom_tts
        )
        
        audio_preparer = AudioPayloadPreparer()

        # Set up the audio playback function
        def _websocket_audio_handler(sentence: str | None, filepath: str | None) -> None:
            if filepath is None:
                logger.info("No audio to be streamed. Response is empty.")
                return

            if sentence is None:
                sentence = ""
            
            logger.info(f"Playing {filepath}...")
            payload, duration = audio_preparer.prepare_audio_payload(
                audio_path=filepath,
                display_text=sentence,
                expression_list=l2d.extract_emotion(sentence),
            )
            logger.info("Payload prepared")

            async def _send_audio():
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(duration)

            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(_send_audio())
            new_loop.close()

            logger.info("Audio played")

        open_llm_vtuber.set_audio_output_func(_websocket_audio_handler)
        return l2d, open_llm_vtuber, audio_preparer

    def _setup_routes(self):
        """Sets up the WebSocket and broadcast routes."""

        # the connection between this server and the frontend client
        # The version 2 of the client-ws. Introduces breaking changes.
        # This route will initiate its own main.py instance and conversation loop
        @self.app.websocket("/client-ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            await websocket.send_text(
                json.dumps({"type": "full-text", "text": "Connection established"})
            )

            self.connected_clients.append(websocket)
            print("Connection established")

            # Initialize components
            l2d, open_llm_vtuber, _ = self._initialize_components(websocket)

            await websocket.send_text(
                json.dumps({"type": "set-model", "text": l2d.model_info})
            )
            print("Model set")
            received_data_buffer = np.array([])
            # start mic
            await websocket.send_text(
                json.dumps({"type": "control", "text": "start-mic"})
            )

            conversation_task = None

            try:
                while True:
                    print(".", end="")
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    # print(f"\033\n Received ws req: {data.get('type')}\033[0m\n")

                    if data.get("type") == "interrupt-signal":
                        print("Received interrupt signal")
                        if conversation_task is not None:
                            try:
                                print(
                                    "\033[91mInterrupting current conversation...",
                                    "heard response: \n",
                                    data.get("text"),
                                    "\033[0m\n",
                                )
                                # 同步调用中断
                                await asyncio.to_thread(
                                    open_llm_vtuber.interrupt,
                                    data.get("text")
                                )
                                
                                # 等待当前��完成或取消
                                try:
                                    await asyncio.wait_for(conversation_task, timeout=2.0)
                                except asyncio.TimeoutError:
                                    conversation_task.cancel()
                                    
                                print("Interrupt processed successfully")
                                
                            except Exception as e:
                                logger.error(f"Error during interrupt: {e}")
                                # 确保系统恢复到可用状态
                                open_llm_vtuber._continue_exec_flag.set()

                    elif data.get("type") == "mic-audio-data":
                        received_data_buffer = np.append(
                            received_data_buffer,
                            np.array(
                                list(data.get("audio").values()), dtype=np.float32
                            ),
                        )
                        print("*", end="")

                    elif data.get("type") == "mic-audio-end":
                        print("Received audio data end from front end.")
                        await websocket.send_text(
                            json.dumps({"type": "full-text", "text": "Thinking..."})
                        )
                        audio = received_data_buffer
                        received_data_buffer = np.array([])

                        async def _run_conversation():
                            try:
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "control",
                                            "text": "conversation-chain-start",
                                        }
                                    )
                                )
                                await asyncio.to_thread(
                                    open_llm_vtuber.conversation_chain,
                                    user_input=audio,
                                )
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "control",
                                            "text": "conversation-chain-end",
                                        }
                                    )
                                )
                                print("One Conversation Loop Completed")
                            except asyncio.CancelledError:
                                print("Conversation task was cancelled.")
                            except InterruptedError as e:
                                print(f"😢Conversation was interrupted. {e}")

                        conversation_task = asyncio.create_task(_run_conversation())
                    elif data.get("type") == "fetch-configs":
                        config_files = self._scan_config_alts_directory()
                        await websocket.send_text(
                            json.dumps({"type": "config-files", "files": config_files})
                        )
                    elif data.get("type") == "switch-config":
                        config_file = data.get("file")
                        if config_file:
                            result = await self._handle_config_switch(websocket, config_file)
                            if result:
                                l2d, open_llm_vtuber = result
                                
                    elif data.get("type") == "fetch-backgrounds":
                        bg_files = self._scan_bg_directory()
                        await websocket.send_text(
                            json.dumps({"type": "background-files", "files": bg_files})
                        )
                    else:
                        print("Unknown data type received.")

            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
                open_llm_vtuber = None

    def _scan_config_alts_directory(self) -> List[str]:
        config_files = ["conf.yaml"]  # default config file
        config_alts_dir = self.open_llm_vtuber_main_config.get(
            "CONFIG_ALTS_DIR", "config_alts"
        )
        for root, _, files in os.walk(config_alts_dir):
            for file in files:
                if file.endswith(".yaml"):
                    config_files.append(file)
        return config_files

    def _load_config_from_file(self, filename: str) -> Dict:
        """
        Load configuration from a YAML file with robust encoding handling.
        
        Args:
            filename: Name of the config file
            
        Returns:
            Dict: Loaded configuration or None if loading fails
        """
        if filename == "conf.yaml":
            return load_config_with_env("conf.yaml")
        
        config_alts_dir = self.open_llm_vtuber_main_config.get("CONFIG_ALTS_DIR", "config_alts")
        file_path = os.path.join(config_alts_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Config file not found: {file_path}")
            return None
            
        # Try common encodings first
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'ascii']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    break
            except UnicodeDecodeError:
                continue
                
        if content is None:
            # Try detecting encoding as last resort
            try:
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                detected = chardet.detect(raw_data)
                if detected['encoding']:
                    content = raw_data.decode(detected['encoding'])
            except Exception as e:
                logger.error(f"Error detecting encoding for config file {file_path}: {e}")
                return None

        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML from {file_path}: {e}")
            return None

    def _scan_bg_directory(self) -> List[str]:
        bg_files = []
        bg_dir = os.path.join("static", "bg")
        for root, _, files in os.walk(bg_dir):
            for file in files:
                if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                    bg_files.append(file)
        return bg_files

    def _mount_static_files(self):
        """Mounts static file directories."""
        self.app.mount(
            "/live2d-models",
            StaticFiles(directory="live2d-models"),
            name="live2d-models",
        )
        self.app.mount("/", StaticFiles(directory="./static", html=True), name="static")

    def run(self, host: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
        """Runs the FastAPI application using Uvicorn."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, log_level=log_level)

    @staticmethod
    def clean_cache():
        """Clean the cache directory by removing and recreating it."""
        cache_dir = "./cache"
        if (os.path.exists(cache_dir)):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)

    def clean_up(self):
        """Clean up resources before shutting down"""
        self.clean_cache()
        # Clear model cache
        self.model_manager.cache.clear()


def load_config_with_env(path) -> dict:
    """
    Load the configuration file with environment variables.

    Parameters:
    - path (str): The path to the configuration file.

    Returns:
    - dict: The configuration dictionary.

    Raises:
    - FileNotFoundError if the configuration file is not found.
    - yaml.YAMLError if the configuration file is not a valid YAML file.
    """
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    # Match ${VAR_NAME}
    pattern = re.compile(r"\$\{(\w+)\}")

    # replace ${VAR_NAME} with os.getenv('VAR_NAME')
    def replacer(match):
        env_var = match.group(1)
        return os.getenv(
            env_var, match.group(0)
        )  # return the original string if the env var is not found

    content = pattern.sub(replacer, content)

    # Load the yaml file
    return yaml.safe_load(content)


class ModelCache:
    """管理 ASR 和 TTS 模型的缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        
    def get(self, key: str) -> Any:
        """获取缓存的模型"""
        return self._cache.get(key)
        
    def set(self, key: str, model: Any) -> None:
        """设置缓存的模型"""
        self._cache[key] = model
        
    def remove(self, key: str) -> None:
        """移除缓存的模型"""
        self._cache.pop(key, None)
        
    def clear(self) -> None:
        """清除所有缓存的模型"""
        self._cache.clear()

class ModelManager:
    """管理模型的初始化、更新和缓存"""
    
    def __init__(self, config: Dict):
        self.config = config
        self._old_config = config.copy()  # 保存初始配置的副本
        self.cache = ModelCache()
        
    def initialize_models(self) -> None:
        """初始化 ASR 和 TTS 模型"""
        if self.config.get("VOICE_INPUT_ON", False):
            self._init_asr()
        if self.config.get("TTS_ON", False):
            self._init_tts()
            
    def _init_asr(self) -> None:
        """初始化 ASR 模型"""
        from asr.asr_factory import ASRFactory
        asr_model = self.config.get("ASR_MODEL")
        asr_config = self.config.get(asr_model, {})
        self.cache.set('asr', ASRFactory.get_asr_system(asr_model, **asr_config))
        logger.info(f"ASR model {asr_model} loaded successfully")
        
    def _init_tts(self) -> None:
        """初始化 TTS 模型"""
        from tts.tts_factory import TTSFactory
        tts_model = self.config.get("TTS_MODEL")
        tts_config = self.config.get(tts_model, {})
        self.cache.set('tts', TTSFactory.get_tts_engine(tts_model, **tts_config))
        logger.info(f"TTS model {tts_model} loaded successfully")
        
    def update_models(self, new_config: Dict) -> None:
        """根据新配置更新模型"""
        try:
            # 确保 _old_config 存在
            if not hasattr(self, '_old_config'):
                self._old_config = self.config.copy()
                
            # 检查并更新模型
            if self._should_reinit_asr(new_config):
                self.config = new_config  # 更新当前配置
                self._update_asr()
            if self._should_reinit_tts(new_config):
                self.config = new_config  # 更新当前配置
                self._update_tts()
                
            # 更新旧配置以供下次比较
            self._old_config = new_config.copy()
            self.config = new_config
            
        except Exception as e:
            logger.error(f"Error during model update: {e}")
            raise
        
    def _should_reinit_asr(self, new_config: Dict) -> bool:
        """检查是否需要重新初始化 ASR"""
        # 检查基本设置是否改变
        if self._old_config.get("VOICE_INPUT_ON") != new_config.get("VOICE_INPUT_ON"):
            return True
            
        # 检查 ASR 模型是否改变
        old_model = self._old_config.get("ASR_MODEL")
        new_model = new_config.get("ASR_MODEL")
        if old_model != new_model:
            return True
            
        # 如果模型相同，检查该模型的所有子配置是否改变
        if old_model:  # 确保模型名不为空
            old_model_config = self._old_config.get(old_model, {})
            new_model_config = new_config.get(old_model, {})
            
            # 深度比较所有子配置
            if old_model_config != new_model_config:
                logger.info(f"ASR model {old_model} settings changed")
                # 可以详细记录具体哪些设置发生了变化
                for key in set(old_model_config.keys()) | set(new_model_config.keys()):
                    if old_model_config.get(key) != new_model_config.get(key):
                        logger.debug(f"ASR setting changed - {key}: {old_model_config.get(key)} -> {new_model_config.get(key)}")
                return True
                
        return False
        
    def _should_reinit_tts(self, new_config: Dict) -> bool:
        """检查是否需要重新初始化 TTS"""
        # 检查基本设置是否改变
        if self._old_config.get("TTS_ON") != new_config.get("TTS_ON"):
            return True
            
        # 检查 TTS 模型是否改变
        old_model = self._old_config.get("TTS_MODEL")
        new_model = new_config.get("TTS_MODEL")
        if old_model != new_model:
            return True
            
        # 如果模型相同，检查该模型的所有子配置是否改变
        if old_model:  # 确保模型名不为空
            old_model_config = self._old_config.get(old_model, {})
            new_model_config = new_config.get(old_model, {})
            
            # 深度比较所有子配置
            if old_model_config != new_model_config:
                logger.info(f"TTS model {old_model} settings changed")
                # 可以详细记录具体哪些设置发生了变化
                for key in set(old_model_config.keys()) | set(new_model_config.keys()):
                    if old_model_config.get(key) != new_model_config.get(key):
                        logger.debug(f"TTS setting changed - {key}: {old_model_config.get(key)} -> {new_model_config.get(key)}")
                return True
                
        return False
        
    def _update_asr(self) -> None:
        """更新 ASR 模型"""
        if self.config.get("VOICE_INPUT_ON", False):
            logger.info("Reinitializing ASR...")
            self._init_asr()
        else:
            logger.info("ASR disabled in new configuration")
            self.cache.remove('asr')
            
    def _update_tts(self) -> None:
        """更新 TTS 模型"""
        if self.config.get("TTS_ON", False):
            logger.info("Reinitializing TTS...")
            self._init_tts()
        else:
            logger.info("TTS disabled in new configuration")
            self.cache.remove('tts')


if __name__ == "__main__":

    atexit.register(WebSocketServer.clean_cache)

    # Load configurations from yaml file
    config = load_config_with_env("conf.yaml")

    config["LIVE2D"] = True  # make sure the live2d is enabled

    # Initialize and run the WebSocket server
    server = WebSocketServer(open_llm_vtuber_main_config=config)
    server.run(host=config["HOST"], port=config["PORT"])
