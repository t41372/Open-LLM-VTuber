import asyncio
import threading
from websocket import WebSocket
from asr.asr_factory import ASRFactory
from asr.asr_interface import ASRInterface
from loguru import logger
from translate.translate_interface import TranslateInterface
from utils.InputQueue import InputQueue
from utils.OutputQueue import OutputQueue


class VoiceListener:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(VoiceListener, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    config: dict | None
    asr: ASRInterface | None
    translator: TranslateInterface | None
    EXEC_FLAG_CHECK_TIMEOUT = 5  # seconds

    def __init__(self, configs: dict | None = None,
                 custom_asr: ASRInterface | None = None,
                 websocket: WebSocket | None = None) -> None:
        """
        Initializes the VoiceListener with threading and asyncio compatibility.
        """
        if not self._initialized:
            self.config = configs
            self.verbose = self.config.get("VERBOSE", False)
            self.websocket = websocket
            self.stop_event = threading.Event()
            self.input_queue = InputQueue()
            self.initialized = True
        # Init ASR if voice input is on.
        if self.config.get("VOICE_INPUT_ON", False):
            if custom_asr is None:
                logger.info("Using default ASR")
                self.asr = self.init_asr()
            else:
                logger.info("Using custom ASR")
                self.asr = custom_asr
        else:
            self.asr = None

        # Create a thread for user input
        self.thread = threading.Thread(target=self.run_user_input_loop, daemon=True)

    def init_asr(self) -> ASRInterface:
        asr_model = self.config.get("ASR_MODEL")
        asr_config = self.config.get(asr_model, {})
        if asr_model == "AzureASR":
            import api_keys
            asr_config = {
                "callback": print,
                "subscription_key": api_keys.AZURE_API_Key,
                "region": api_keys.AZURE_REGION,
            }

        asr = ASRFactory.get_asr_system(asr_model, **asr_config)
        return asr

    def start(self):
        """Starts the queue processing thread."""
        logger.info("Starting ASR thread...")
        self.thread.start()

    def run_user_input_loop(self):
        """Runs the asyncio event loop for get_user_input in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.get_user_input_loop())
        except Exception as e:
            logger.error(f"Error in user input loop: {e}")
        finally:
            loop.close()

    async def get_user_input_loop(self):
        """Continuously gets user input asynchronously."""
        while not self.stop_event.is_set():
            try:
                logger.info("Waiting for user input...")
                user_input = self.input_queue.get_input()
                result = self.asr.()
                self.input_queue.add_input(result)

            except Exception as e:
                logger.error(f"Error in transcribing user input: {e}")

    def stop(self):
        """Stops the thread gracefully."""
        self.stop_event.set()
        self.thread.join()
        logger.info("Stopping VoiceListener...")
