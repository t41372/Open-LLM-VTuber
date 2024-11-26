import os
import sys
import re
import random
import shutil
import atexit
import threading
import queue
import uuid
from typing import Callable, Iterator, Optional, Dict
from fastapi import FastAPI, WebSocket, HTTPException
from loguru import logger
import numpy as np
import yaml
import chardet
from pydantic import BaseModel  # 导入 BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.audio_preprocessor import audio_filter

import __init__
from asr.asr_factory import ASRFactory
from asr.asr_interface import ASRInterface
from live2d_model import Live2dModel
from llm.llm_factory import LLMFactory
from llm.llm_interface import LLMInterface
from prompts import prompt_loader
from tts.tts_factory import TTSFactory
from tts.tts_interface import TTSInterface
from translate.translate_interface import TranslateInterface
from translate.translate_factory import TranslateFactory

app = FastAPI()
thread_pool = ThreadPoolExecutor()

class ChatInput(BaseModel):  # 修改为 Pydantic 模型
    text: str
    priority: int

class OpenLLMVTuberMain:
    """
    The main class for the OpenLLM VTuber.
    It initializes the Live2D controller, ASR, TTS, and LLM based on the provided configuration.
    Run `conversation_chain` to start one conversation (user_input -> llm -> speak).

    Attributes:
    - config (dict): The configuration dictionary.
    - llm (LLMInterface): The LLM instance.
    - asr (ASRInterface): The ASR instance.
    - tts (TTSInterface): The TTS instance.
    """

    EXEC_FLAG_CHECK_TIMEOUT = 8  # seconds

    def __init__(
        self,
        configs: dict,
        custom_asr: ASRInterface | None = None,
        custom_tts: TTSInterface | None = None,
        websocket: WebSocket | None = None,
    ) -> None:
        logger.info(f"t41372/Open-LLM-VTuber, version {__init__.__version__}")

        self.config: dict = configs
        self.verbose = self.config.get("VERBOSE", False)
        self.websocket = websocket
        self.live2d: Live2dModel | None = self.init_live2d()
        self._continue_exec_flag = threading.Event()
        self._continue_exec_flag.set()  # Set the flag to continue execution
        self.session_id: str = str(uuid.uuid4().hex)
        self.heard_sentence: str = ""

        # 初始化音频处理相关的属性
        self._task_queue = None
        self._processing_audio = threading.Event()
        self._consumer_thread = None

        # Init ASR if voice input is on.
        self.asr: ASRInterface | None
        if self.config.get("VOICE_INPUT_ON", False):
            # if custom_asr is provided, don't init asr and use it instead.
            if custom_asr is None:
                self.asr = self.init_asr()
            else:
                print("Using custom ASR")
                self.asr = custom_asr
        else:
            self.asr = None

        # Init TTS if TTS is on.
        self.tts: TTSInterface
        if self.config.get("TTS_ON", False):
            # if custom_tts is provided, don't init tts and use it instead.
            if custom_tts is None:
                self.tts = self.init_tts()
            else:
                print("Using custom TTS")
                self.tts = custom_tts
        else:
            self.tts = None

        # Init Translator if enabled
        self.translator: TranslateInterface | None
        if self.config.get("TRANSLATE_AUDIO", False):
            try:
                translate_provider = self.config.get("TRANSLATE_PROVIDER", "DeepLX")
                self.translator = TranslateFactory.get_translator(
                    translate_provider=translate_provider,
                    **self.config.get(translate_provider, {}),
                )
            except Exception as e:
                print(f"Error initializing Translator: {e}")
                print("Proceed without Translator.")
                self.translator = None
        else:
            self.translator = None

        self.llm: LLMInterface = self.init_llm()

    # Initialization methods

    def init_live2d(self) -> Live2dModel | None:
        if not self.config.get("LIVE2D", False):
            return None
        try:
            live2d_model_name = self.config.get("LIVE2D_MODEL")
            live2d_controller = Live2dModel(live2d_model_name)
        except Exception as e:
            print(f"Error initializing Live2D: {e}")
            print("Proceed without Live2D.")
            return None
        return live2d_controller

    def init_llm(self) -> LLMInterface:
        llm_provider = self.config.get("LLM_PROVIDER")
        llm_config = self.config.get(llm_provider, {})
        system_prompt = self.get_system_prompt()

        llm = LLMFactory.create_llm(
            llm_provider=llm_provider, SYSTEM_PROMPT=system_prompt, **llm_config
        )
        return llm

    def init_asr(self) -> ASRInterface:
        asr_model = self.config.get("ASR_MODEL")
        asr_config = self.config.get(asr_model, {})
        asr = ASRFactory.get_asr_system(asr_model, **asr_config)
        return asr

    def init_tts(self) -> TTSInterface:
        tts_model = self.config.get("TTS_MODEL", "pyttsx3TTS")
        tts_config = self.config.get(tts_model, {})
        return TTSFactory.get_tts_engine(tts_model, **tts_config)

    def set_audio_output_func(
        self, audio_output_func: Callable[[Optional[str], Optional[str]], None]
    ) -> None:
        self._play_audio_file = audio_output_func

    def get_system_prompt(self) -> str:
        if self.config.get("PERSONA_CHOICE"):
            system_prompt = prompt_loader.load_persona(
                self.config.get("PERSONA_CHOICE")
            )
        else:
            system_prompt = self.config.get("DEFAULT_PERSONA_PROMPT_IN_YAML")

        if self.live2d is not None:
            system_prompt += prompt_loader.load_util(
                self.config.get("LIVE2D_Expression_Prompt")
            ).replace("[<insert_emomap_keys>]", self.live2d.emo_str)

        if self.verbose:
            print("\n === System Prompt ===")
            print(system_prompt)

        return system_prompt

    # Main conversation methods

    def conversation_chain(self, user_input: str | np.ndarray | None = None) -> str:
        if not self._continue_exec_flag.wait(
            timeout=self.EXEC_FLAG_CHECK_TIMEOUT
        ):  # Wait for the flag to be set
            print(
                ">> Execution flag not set. In interruption state for too long. Resetting the flag and exiting the conversation chain."
            )
            self._continue_exec_flag.set()
            raise InterruptedError(
                "Conversation chain interrupted. Wait flag timeout reached."
            )

        color_code = random.randint(0, 3)
        c = [None] * 4
        c[0] = "\033[91m"
        c[1] = "\033[94m"
        c[2] = "\033[92m"
        c[3] = "\033[0m"

        print(f"{c[color_code]}New Conversation Chain started!")

        if user_input is None:
            user_input = self.get_user_input()
        elif isinstance(user_input, np.ndarray):
            print("transcribing...")
            user_input = self.asr.transcribe_np(user_input)

        if user_input.strip().lower() == self.config.get("EXIT_PHRASE", "exit").lower():
            print("Exiting...")
            exit()

        print(f"User input: {user_input}")

        chat_completion: Iterator[str] = self.llm.chat_iter(user_input)

        if not self.config.get("TTS_ON", False):
            full_response = ""
            for char in chat_completion:
                if not self._continue_exec_flag.is_set():
                    self._interrupt_post_processing()
                    print("\nInterrupted!")
                    return None
                full_response += char
                print(char, end="")
            return full_response

        full_response = self.speak(chat_completion)
        if self.verbose:
            print(f"\nComplete response: [\n{full_response}\n]")

        print(f"{c[color_code]}Conversation completed.")
        return full_response

    def get_user_input(self) -> str:
        if self.config.get("VOICE_INPUT_ON", False):
            print("Listening from the microphone...")
            return self.asr.transcribe_with_local_vad()
        else:
            return input("\n>> ")

    def speak(self, chat_completion: Iterator[str]) -> str:
        full_response = ""
        if self.config.get("SAY_SENTENCE_SEPARATELY", True):
            full_response = self.speak_by_sentence_chain(chat_completion)
        else:
            full_response = ""
            for char in chat_completion:
                if not self._continue_exec_flag.is_set():
                    print("\nInterrupted!")
                    self._interrupt_post_processing()
                    return None
                print(char, end="")
            full_response += char
            print("\n")
            filename = self._generate_audio_file(full_response, "temp")

            if self._continue_exec_flag.is_set():
                self._play_audio_file(
                    sentence=full_response,
                    filepath=filename,
                )
            else:
                self._interrupt_post_processing()

        return full_response

    def _generate_audio_file(self, sentence: str, file_name_no_ext: str) -> str | None:
        if self.verbose:
            print(f">> generating {file_name_no_ext}...")

        if not self.tts:
            return None

        if self.live2d:
            sentence = self.live2d.remove_emotion_keywords(sentence)

        if sentence.strip() == "":
            return None

        return self.tts.generate_audio(sentence, file_name_no_ext=file_name_no_ext)

    def _play_audio_file(self, sentence: str | None, filepath: str | None) -> None:
        if filepath is None:
            print("No audio to be streamed. Response is empty.")
            return

        if sentence is None:
            sentence = ""

        try:
            if self.verbose:
                print(f">> Playing {filepath}...")
            self.tts.play_audio_file_local(filepath)

            self.tts.remove_file(filepath, verbose=self.verbose)
        except ValueError as e:
            if str(e) == "Audio is empty or all zero.":
                print("No audio to be streamed. Response is empty.")
            else:
                raise e
        except Exception as e:
            print(f"Error playing the audio file {filepath}: {e}")

    def speak_by_sentence_chain(self, chat_completion: Iterator[str]) -> str:
        task_queue = queue.Queue()
        full_response = [""]
        interrupted_error_event = threading.Event()
        self._processing_audio = threading.Event()
        self._task_queue = task_queue
        self._consumer_thread = None

        def producer_worker():
            try:
                sentence_buffer = ""
                for char in chat_completion:
                    if not self._continue_exec_flag.is_set():
                        raise InterruptedError("Producer interrupted")

                    print(char, end="", flush=True)
                    sentence_buffer += char
                    full_response[0] += char

                    if self.is_complete_sentence(sentence_buffer):
                        if not self._continue_exec_flag.is_set():
                            raise InterruptedError("Producer interrupted")
                        tts_target_sentence=sentence_buffer
                        tts_target_sentence = audio_filter(
                                tts_target_sentence,
                                translator=(
                                    self.translator
                                    if self.config.get("TRANSLATE_AUDIO", False)
                                    else None
                                ),
                                remove_special_char=self.config.get(
                                    "REMOVE_SPECIAL_CHAR", True
                                ),
                            )
                        print("tts_target_sentence:"+tts_target_sentence)
                        audio_info = self._prepare_audio(tts_target_sentence)
                        if audio_info:
                            self._processing_audio.set()
                            task_queue.put(audio_info)
                        sentence_buffer = ""

                if sentence_buffer.strip():
                    tts_target_sentence=sentence_buffer
                    tts_target_sentence = audio_filter(
                            tts_target_sentence,
                            translator=(
                                self.translator
                                if self.config.get("TRANSLATE_AUDIO", False)
                                else None
                            ),
                            remove_special_char=self.config.get(
                                "REMOVE_SPECIAL_CHAR", True
                            ),
                        )
                    audio_info = self._prepare_audio(tts_target_sentence)
                    
                    if audio_info:
                        self._processing_audio.set()
                        task_queue.put(audio_info)

            except InterruptedError as e:
                interrupted_error_event.set()
                print(f"\nProducer interrupted: {e}")
            finally:
                task_queue.put(None)

        def consumer_worker():
            while True:
                try:
                    audio_info = task_queue.get()
                    if audio_info is None:
                        break

                    if not self._continue_exec_flag.is_set():
                        break

                    self._play_audio_file(
                        sentence=audio_info["sentence"],
                        filepath=audio_info["audio_filepath"]
                    )
                    task_queue.task_done()

                except Exception as e:
                    print(f"Consumer error: {e}")
                    break
                finally:
                    self._processing_audio.clear()

        producer = threading.Thread(target=producer_worker)
        consumer = threading.Thread(target=consumer_worker)
        self._consumer_thread = consumer

        producer.start()
        consumer.start()

        producer.join()
        task_queue.put(None)  # 确保消费者会退出
        consumer.join()

        self._consumer_thread = None
        self._processing_audio.clear()
        while not task_queue.empty():
            try:
                task_queue.get_nowait()
            except queue.Empty:
                break

        return full_response[0]   

    def is_processing_audio(self) -> bool:
        """判断是否正在处理或播放音频"""
        # 检查所有可能的处理状态
        if self._task_queue is not None and not self._task_queue.empty():
            return True

        if self._processing_audio.is_set():
            return True

        if self._consumer_thread is not None and self._consumer_thread.is_alive():
            return True

        return False
        
    def interrupt(self, heard_text: str | None = None) -> None:
        """
        中断当前的对话和音频播放
        Args:
            heard_text: 已经听到的文本，用于记录
        """
        print("\nInterrupting current conversation...")
        self._continue_exec_flag.clear()
        self.heard_sentence = heard_text if heard_text else ""

        # 清理音频处理状态
        if self._processing_audio.is_set():
            self._processing_audio.clear()

        # 清空任务队列
        if self._task_queue:
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                    self._task_queue.task_done()
                except queue.Empty:
                    break

        # 停止当前消费者线程
        if self._consumer_thread and self._consumer_thread.is_alive():
            self._task_queue.put(None)  # 确保消费者会退出
            self._consumer_thread.join(timeout=1.0)  # 等待消费者线程结束，设置超时
            self._consumer_thread = None

        # 重置执行标志
        self._continue_exec_flag.set()

        print("Interruption completed")

    def _interrupt_post_processing(self) -> None:
        """
        中断后的清理工作
        """
        self._continue_exec_flag.set()
        self._processing_audio.clear()

        # 清空任务队列
        if self._task_queue:
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                    self._task_queue.task_done()
                except queue.Empty:
                    break

    def _check_interrupt(self):
        if not self._continue_exec_flag.is_set():
            raise InterruptedError("Conversation chain interrupted: checked")

    def _prepare_audio(self, sentence: str) -> Optional[Dict]:
        """准备音频文件并返回音频信息"""
        if not sentence.strip():
            return None

        tts_target_sentence = sentence
        if self.translator and self.config.get("TRANSLATE_AUDIO", False):
            tts_target_sentence = self.translator.translate(tts_target_sentence)

        audio_filepath = self._generate_audio_file(
            tts_target_sentence, 
            file_name_no_ext=uuid.uuid4()
        )

        if audio_filepath:
            return {
                "sentence": sentence,
                "audio_filepath": audio_filepath
            }
        return None

    def is_complete_sentence(self, text: str):
        white_list = [
            "...",
            "Dr.",
            "Mr.",
            "Ms.",
            "Mrs.",
            "Jr.",
            "Sr.",
            "St.",
            "Ave.",
            "Rd.",
            "Blvd.",
            "Dept.",
            "Univ.",
            "Prof.",
            "Ph.D.",
            "M.D.",
            "U.S.",
            "U.K.",
            "U.N.",
            "E.U.",
            "U.S.A.",
            "U.K.",
            "U.S.S.R.",
            "U.A.E.",
        ]

        for item in white_list:
            if text.strip().endswith(item):
                return False

        punctuation_blacklist = [
            ".",
            "?",
            "!",
            "。",
            "；",
            "？",
            "！",
            "…",
            "〰",
            "〜",
            "～",
            "！",
        ]
        return any(text.strip().endswith(punct) for punct in punctuation_blacklist)

    def clean_cache(self):
        cache_dir = "./cache"
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        os.makedirs(cache_dir)

    def load_and_apply_config(self, config_file: str) -> None:
        with open(config_file, "r", encoding="utf-8") as file:
            new_config = yaml.safe_load(file)

        self.config.update(new_config)

        self.live2d = self.init_live2d()
        self.asr = self.init_asr()
        self.tts = self.init_tts()
        self.translator = self.init_translator()
        self.llm = self.init_llm()

    def init_translator(self) -> TranslateInterface | None:
        if self.config.get("TRANSLATE_AUDIO", False):
            try:
                translate_provider = self.config.get("TRANSLATE_PROVIDER", "DeepLX")
                translator = TranslateFactory.get_translator(
                    translate_provider=translate_provider,
                    **self.config.get(translate_provider, {}),
                )
                return translator
            except Exception as e:
                print(f"Error initializing Translator: {e}")
                print("Proceed without Translator.")
                return None
        else:
            return None


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
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    # Try common encodings first
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "ascii"]
    content = None

    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as file:
                content = file.read()
                break
        except UnicodeDecodeError:
            continue

    if content is None:
        # Try detecting encoding as last resort
        try:
            with open(path, "rb") as file:
                raw_data = file.read()
            detected = chardet.detect(raw_data)
            if detected["encoding"]:
                content = raw_data.decode(detected["encoding"])
        except Exception as e:
            logger.error(f"Error detecting encoding for config file {path}: {e}")
            raise UnicodeError(f"Failed to decode config file {path} with any encoding")

    # Match ${VAR_NAME}
    pattern = re.compile(r"\$\{(\w+)\}")

    # replace ${VAR_NAME} with os.getenv('VAR_NAME')
    def replacer(match):
        env_var = match.group(1)
        return os.getenv(env_var, match.group(0))

    content = pattern.sub(replacer, content)

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML from {path}: {e}")
        raise

async def process_conversation_async(vtuber_main: OpenLLMVTuberMain, text: str):
    """异步处理对话任务"""
    try:
        # 在线程池中运行会话链
        await asyncio.get_event_loop().run_in_executor(
            thread_pool, 
            vtuber_main.conversation_chain,
            text
        )
    except Exception as e:
        logger.error(f"Error in conversation chain: {e}")
        # 确保在错误时重置标志
        vtuber_main._continue_exec_flag.set()
        if hasattr(vtuber_main, '_processing_audio'):
            vtuber_main._processing_audio.clear()
        if hasattr(vtuber_main, '_task_queue'):
            while not vtuber_main._task_queue.empty():
                try:
                    vtuber_main._task_queue.get_nowait()
                except queue.Empty:
                    break

if __name__ == "__main__":
    logger.add(sys.stderr, level="DEBUG")

    config = load_config_with_env("conf.yaml")

    vtuber_main = OpenLLMVTuberMain(config)

    atexit.register(vtuber_main.clean_cache)

    def _interrupt_on_i():
        while input(">>> say i and press enter to interrupt: ") == "i":
            print("\n\n!!!!!!!!!! interrupt !!!!!!!!!!!!...\n")
            print("Heard sentence: ", vtuber_main.heard_sentence)
            vtuber_main.interrupt(vtuber_main.heard_sentence)

    if config.get("VOICE_INPUT_ON", False):
        threading.Thread(target=_interrupt_on_i).start()

    print("tts on: ", vtuber_main.config.get("TTS_ON", False))
    while True:
        try:
            vtuber_main.conversation_chain()
        except InterruptedError as e:
            print(f"😢Conversation was interrupted. {e}")
            continue

vtuber_main: Optional[OpenLLMVTuberMain] = None

@app.post("/textinput")
async def chat_input(chat_input: ChatInput):
    global vtuber_main
    if not vtuber_main:
        return {"error_code": 5001, "detail": "VTuber main instance not initialized"}

    try:
        if chat_input.priority not in [0, 1]:
            return {"error_code": 400, "detail": "Priority must be 0 or 1"}

        print(f"\nReceived request - Priority: {chat_input.priority}")

        # 检查系统状态 - 使用现有的 is_processing_audio 方法
        is_busy = not vtuber_main._continue_exec_flag.is_set() or vtuber_main.is_processing_audio()

        print(f"Current state - Busy: {is_busy} (Continue Flag: {vtuber_main._continue_exec_flag.is_set()}, Processing Audio: {vtuber_main.is_processing_audio()})")

        # 获取当前连接的WebSocket客户端
        if hasattr(vtuber_main, 'websocket_server'):
            clients = vtuber_main.websocket_server.get_connected_clients()
            if not clients:
                return {"error_code": 4002, "detail": "No WebSocket clients connected"}

            # 设置WebSocket连接
            vtuber_main.websocket = clients[0]

        if chat_input.priority == 1:
            print("Priority 1 request - forcing stop of current process")
            vtuber_main.interrupt(vtuber_main.heard_sentence)
            vtuber_main._continue_exec_flag.set()
            # 异步启动新的对话任务
            asyncio.create_task(process_conversation_async(vtuber_main, chat_input.text))
            return {"error_code": 0, "status": "accepted", "message": "Priority 1 request accepted"}

        if is_busy:
            print("Rejecting priority 0 request - system busy")
            return {"error_code": 4001, "detail": "Conversation or audio playback in progress"}

        # 异步启动新的对话任务
        asyncio.create_task(process_conversation_async(vtuber_main, chat_input.text))
        return {"error_code": 0, "status": "accepted", "message": "Request is being processed"}

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {"error_code": 5000, "detail": f"Internal server error: {str(e)}"}