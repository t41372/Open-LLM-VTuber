import threading

from websocket import WebSocket

from asr.asr_factory import ASRFactory
from asr.asr_interface import ASRInterface
from loguru import logger

from translate.translate_interface import TranslateInterface
from utils.InputQueue import InputQueue


class VoiceListener:
    config: dict | None
    asr: ASRInterface | None
    translator: TranslateInterface | None
    _continue_exec_flag: threading.Event
    EXEC_FLAG_CHECK_TIMEOUT = 5  # seconds

    def __init__(self, configs: dict | None = None,
                 custom_asr: ASRInterface | None = None,
                 websocket: WebSocket | None = None) -> None:
        """
        Initializes the VoiceListener as a separate thread.
        :param pause_threshold: The time threshold for considering pauses in speech, in seconds.
        """
        super(VoiceListener, self).__init__()
        self.running = None
        self.config = configs
        self.thread = threading.Thread(target=self.get_user_input)
        self.verbose = self.config.get("VERBOSE", False)
        self.websocket = websocket
        self.stop_event = threading.Event()
        self.input_queue = InputQueue()
        # Init ASR if voice input is on.
        if self.config.get("VOICE_INPUT_ON", False):
            # if custom_asr is provided, don't init asr and use it instead.
            if custom_asr is None:
                logger.info("Using default ASR")
                self.asr = self.init_asr()
            else:
                logger.info("Using custom ASR")
                self.asr = custom_asr
        else:
            self.asr = None

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

    def get_user_input(self) -> str:
        """
        Get user input using the method specified in the configuration file.
        It can be from the console, local microphone, or the browser microphone.

        Returns:
        - str: The user input
        """
        # for live2d with browser, their input are now injected by the server class
        # and they no longer use this method
        if self.config.get("VOICE_INPUT_ON", False):
            # get audio from the local microphone
            logger.info("Listening from the microphone...")
            self.input_queue.add_input(self.asr.transcribe_with_local_vad())

    def stop(self):
        """Stops the thread gracefully."""
        self.stop_event.set()
        self.thread.join()
        logger.info("Stopping VoiceListener...")
        self.running = False
