import os
import queue
import random
import shutil
import threading
import uuid
from typing import Callable, Iterator, Optional

import numpy as np
from fastapi import WebSocket

from live2d_model import Live2dModel
from llm.llm_interface import LLMInterface
from prompts import prompt_loader
from translate.translate_factory import TranslateFactory
from translate.translate_interface import TranslateInterface
from tts.tts_factory import TTSFactory
from tts.tts_interface import TTSInterface


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

    _instance = None  # Class variable to store the singleton instance
    _lock = threading.Lock()  # Lock for thread-safe singleton creation

    config: dict
    llm: "LLMInterface"
    tts: "TTSInterface"
    translator: Optional["TranslateInterface"]
    live2d: Optional["Live2dModel"]
    _continue_exec_flag: threading.Event
    EXEC_FLAG_CHECK_TIMEOUT = 5  # seconds

    def __new__(cls, *args, **kwargs):
        with cls._lock:  # Ensure thread-safe singleton creation
            if cls._instance is None:
                cls._instance = super(OpenLLMVTuberMain, cls).__new__(cls)
        return cls._instance

    def __init__(
            self,
            configs: dict | None = None,
            custom_tts: "TTSInterface" = None,
            websocket: Optional["WebSocket"] = None,
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return  # Skip reinitialization in singleton
        self._initialized = True  # Mark as initialized

        self.config = configs
        self.verbose = self.config.get("VERBOSE", False)
        self.websocket = websocket
        self.live2d = self.init_live2d()
        self._continue_exec_flag = threading.Event()
        self.not_is_blocking_event = threading.Event()
        # clear
        self.not_is_blocking_event.clear()
        self._continue_exec_flag.set()  # Set the flag to continue execution

        # Init TTS if TTS is on
        if self.config.get("TTS_ON", False):
            # Use custom TTS if provided
            if custom_tts is None:
                self.tts = self.init_tts()
            else:
                print("Using custom TTS")
                self.tts = custom_tts
        else:
            self.tts = None

        # Init Translator if enabled
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

        # Initialize the LLM instance
        self.llm = Letta()

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

    def init_tts(self) -> TTSInterface:
        tts_model = self.config.get("TTS_MODEL", "pyttsx3TTS")
        tts_config = self.config.get(tts_model, {})

        if tts_model == "AzureTTS":
            import api_keys

            tts_config = {
                "api_key": api_keys.AZURE_API_Key,
                "region": api_keys.AZURE_REGION,
                "voice": api_keys.AZURE_VOICE,
            }
        tts = TTSFactory.get_tts_engine(tts_model, **tts_config)

        return tts

    def set_audio_output_func(
            self, audio_output_func: Callable[[Optional[str], Optional[str]], None]
    ) -> None:
        """
        Set the audio output function to be used for playing audio files.
        The function should accept two arguments: sentence (str) and filepath (str).

        sentence: str | None
        - The sentence to be displayed on the frontend.
        - If None, empty sentence will be displayed.

        filepath: str | None
        - The path to the audio file to be played.
        - If None, no audio will be played.

        Here is an example of the function:
        ~~~python
        def _play_audio_file(sentence: str | None, filepath: str | None) -> None:
            if filepath is None:
                print("No audio to be streamed. Response is empty.")
                return

            if sentence is None:
                sentence = ""
            print(f">> Playing {filepath}...")
            playsound(filepath)
        ~~~
        """

        self._play_audio_file = audio_output_func

        # def _play_audio_file(self, sentence: str, filepath: str | None) -> None:

    def get_persona_prompt(self) -> str:
        """
        Construct and return the system prompt based on the configuration file.
        """
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

    async def conversation_chain(self, user_input: str | np.ndarray | None = None) -> str:
        """
        One iteration of the main conversation.
        1. Get user input (text or audio) if not provided as an argument
        2. Call the LLM with the user input
        3. Speak (or not)

        Parameters:
        - user_input (str, numpy array, or None): The user input to be used in the conversation. If it's string, it will be considered as user input. If it's a numpy array, it will be transcribed. If it's None, we'll request input from the user.

        Returns:
        - str: The full response from the LLM
        """

        if not self._continue_exec_flag.wait(
                timeout=self.EXEC_FLAG_CHECK_TIMEOUT
        ):  # Wait for the flag to be set
            print(
                ">> Execution flag not set. In interruption state for too long. Exiting conversation chain."
            )
            raise InterruptedError(
                "Conversation chain interrupted. Wait flag timeout reached."
            )

        # Generate a random number between 0 and 3
        color_code = random.randint(0, 3)
        c = [None] * 4
        # Define the color codes for red, blue, green, and white
        c[0] = "\033[91m"
        c[1] = "\033[94m"
        c[2] = "\033[92m"
        c[3] = "\033[0m"

        # Apply the color to the console output
        print(f"{c[color_code]}New Conversation Chain started!")

        # if user_input is not string, make it string
        if user_input.strip().lower() == self.config.get("EXIT_PHRASE", "exit").lower() or user_input is None:
            print("Exiting...")
            exit()
        print(f"User input: {user_input}")
        if not self.not_is_blocking_event.is_set():
            self.not_is_blocking_event.wait()
        chat_completion: Iterator[str] = await self.llm.chat_iter(user_input)

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

    def speak(self, chat_completion: Iterator[str]) -> str:
        """
        Speak the chat completion using the TTS engine.

        Parameters:
        - chat_completion (Iterator[str]): The chat completion to speak

        Returns:
        - str: The full response from the LLM
        """
        if self.config.get("SAY_SENTENCE_SEPARATELY", True):
            full_response = self.speak_by_sentence_chain(chat_completion)
        else:  # say the full response at once? how stupid
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
        """
        Generate an audio file from the given sentence using the TTS engine.

        Parameters:
        - sentence (str): The sentence to generate audio from
        - file_name_no_ext (str): The name of the audio file without the extension

        Returns:
        - str or None: The path to the generated audio file or None if the sentence is empty
        """
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
        """
        Play the audio file either locally or remotely using the Live2D controller if available.

        Parameters:
        - sentence (str): The sentence to display
        - filepath (str): The path to the audio file. If None, no audio will be streamed.
        """

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
        """
        Generate and play the chat completion sentences one by one using the TTS engine.
        Now properly handles interrupts in a multi-threaded environment using the existing _continue_exec_flag.
        """
        task_queue = queue.Queue()
        full_response = [""]  # Use a list to store the full response
        interrupted_error_event = threading.Event()

        def producer_worker():
            try:
                index = 0
                sentence_buffer = ""

                for char in chat_completion:
                    if not self._continue_exec_flag.is_set():
                        raise InterruptedError("Producer interrupted")
                    if char:
                        print(char, end="", flush=True)
                        sentence_buffer += char
                        full_response[0] += char
                        if self.is_complete_sentence(char):
                            if self.verbose:
                                print("\n")
                            if not self._continue_exec_flag.is_set():
                                raise InterruptedError("Producer interrupted")
                            tts_target_sentence = sentence_buffer

                            if self.translator and self.config.get(
                                    "TRANSLATE_AUDIO", False
                            ):
                                print("Translating...")
                                tts_target_sentence = self.translator.translate(
                                    tts_target_sentence
                                )
                                print(f"Translated: {tts_target_sentence}")

                            audio_filepath = self._generate_audio_file(
                                tts_target_sentence, file_name_no_ext=uuid.uuid4()
                            )

                            if not self._continue_exec_flag.is_set():
                                raise InterruptedError("Producer interrupted")
                            audio_info = {
                                "sentence": sentence_buffer,
                                "audio_filepath": audio_filepath,
                            }
                            task_queue.put(audio_info)
                            index += 1
                            sentence_buffer = ""

                # Handle any remaining text in the buffer
                if sentence_buffer:
                    if not self._continue_exec_flag.is_set():
                        raise InterruptedError("Producer interrupted")
                    print("\n")
                    audio_filepath = self._generate_audio_file(
                        sentence_buffer, file_name_no_ext=uuid.uuid4()
                    )
                    audio_info = {
                        "sentence": sentence_buffer,
                        "audio_filepath": audio_filepath,
                    }
                    task_queue.put(audio_info)

            except InterruptedError:
                print("\nProducer interrupted")
                interrupted_error_event.set()
                return  # Exit the function
            except Exception as e:
                print(
                    f"Producer error: Error generating audio for sentence: '{sentence_buffer}'.\n{e}",
                    "Producer stopped\n",
                )
                return
            finally:
                task_queue.put(None)  # Signal end of production

        def consumer_worker():
            heard_sentence = ""

            while True:

                try:
                    if not self._continue_exec_flag.is_set():
                        raise InterruptedError("😱Consumer interrupted")
                    if not self.not_is_blocking_event.is_set():
                        self.not_is_blocking_event.wait()

                    audio_info = task_queue.get(
                        timeout=0.1
                    )  # Short timeout to check for interrupts
                    if audio_info is None:
                        break  # End of production
                    if audio_info:
                        heard_sentence += audio_info["sentence"]
                        self._play_audio_file(
                            sentence=audio_info["sentence"],
                            filepath=audio_info["audio_filepath"],
                        )
                    task_queue.task_done()
                except queue.Empty:
                    continue  # No item available, continue checking for interrupts
                except InterruptedError as e:
                    print(f"\n{str(e)}, stopping worker threads")
                    interrupted_error_event.set()
                    return  # Exit the function
                except Exception as e:
                    print(
                        f"Consumer error: Error playing sentence '{audio_info['sentence']}'.\n {e}"
                    )
                    continue

        producer_thread = threading.Thread(name='Speech Producer Thread', target=producer_worker)
        consumer_thread = threading.Thread(name='Speech Consumer Thread', target=consumer_worker)

        producer_thread.start()
        consumer_thread.start()
        producer_thread.join()
        consumer_thread.join()

        if interrupted_error_event.is_set():
            self._interrupt_post_processing()
            raise InterruptedError(
                "Conversation chain interrupted: consumer model interrupted"
            )

        print("\n\n --- Audio generation and playback completed ---")
        return full_response[0]

    def interrupt(self, heard_sentence: str = "") -> None:
        """Set the interrupt flag to stop the conversation chain.
        Preferably provide the sentences that were already shown or heard by the user before the interrupt so that the LLM can handle the memory properly.

        Parameters:
        - heard_sentence (str): The sentence that was already shown or heard by the user before the interrupt.
            (because apparently the user won't know the rest of the response.)
        """
        self._continue_exec_flag.clear()
        self.llm.handle_interrupt(heard_sentence)

    def _interrupt_post_processing(self) -> None:
        """Perform post-processing tasks (like resetting the continue flag to allow next conversation chain to start) after an interrupt."""
        self._continue_exec_flag.set()  # Reset the interrupt flag

    def _check_interrupt(self):
        """Check if we are in an interrupt state and raise an exception if we are."""
        if not self._continue_exec_flag.is_set():
            raise InterruptedError("Conversation chain interrupted: checked")

    def is_complete_sentence(self, text: str):
        """
        Check if the text is a complete sentence.
        text: str
            the text to check
        """

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


