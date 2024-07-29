import sys
import threading
import queue
from typing import Iterator

from asr.asr_factory import ASRFactory
from asr.asr_interface import ASRInterface
from live2d import Live2dController
from llm.llm_factory import LLMFactory
from llm.llm_interface import LLMInterface
from prompts import prompt_loader
from tts import stream_audio
from tts.tts_factory import TTSFactory
from tts.tts_interface import TTSInterface

import yaml


class OpenLLMVTuberMain:

    config: dict
    llm: LLMInterface
    asr: ASRInterface
    tts: TTSInterface
    live2d: Live2dController

    def __init__(self, configs: dict) -> None:
        self.config = configs
        self.verbose = self.config.get("VERBOSE", False)
        self.live2d = self.init_live2d() if self.config.get("LIVE2D", False) else None
        self.asr = self.init_asr() if self.config.get("VOICE_INPUT_ON", False) else None
        self.tts = self.init_tts() if self.config.get("TTS_ON", False) else None
        self.llm = self.init_llm()

    def init_live2d(self) -> Live2dController:
        live2d_model = self.config.get("LIVE2D_MODEL")
        url = f"{self.config.get('PROTOCOL', 'http://')}{self.config.get('HOST', 'localhost')}:{self.config.get('PORT', 8000)}"
        live2d_controller = Live2dController(live2d_model, base_url=url)
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
        if asr_model == "AzureASR":
            import api_keys

            asr_config = {
                "callback": print,
                "subscription_key": api_keys.AZURE_API_Key,
                "region": api_keys.AZURE_REGION,
            }

        asr = ASRFactory.get_asr_system(asr_model, **asr_config)
        return asr

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

    def get_system_prompt(self) -> str:
        """
        Construct and return the system prompt based on the configuration file.
        """
        if self.config.get("PERSONA_CHOICE"):
            system_prompt = prompt_loader.load_persona(
                self.config.get("PERSONA_CHOICE")
            )
        else:
            system_prompt = self.config.get("DEFAULT_PERSONA_PROMPT_IN_YAML")

        if self.config.get("LIVE2D"):
            system_prompt += prompt_loader.load_util(
                self.config.get("LIVE2D_Expression_Prompt")
            ).replace("[<insert_emomap_keys>]", self.live2d.getEmoMapKeyAsString())

        if self.verbose:
            print("\n === System Prompt ===")
            print(system_prompt)

        return system_prompt

    def conversation_chain(self, user_input: str = None) -> str:
        """
        One iteration of the main conversation.
        1. Get user input (text or audio) if not provided as an argument
        2. Call the LLM with the user input
        3. Speak (or not)
        
        Parameters:
        - user_input (str or None): The user input to be used in the conversation. If None, it will be requested from the user.

        Returns:
        - str: The full response from the LLM
        """

        user_input = self.get_user_input() if user_input is None else user_input
        if user_input.strip().lower() == self.config.get("EXIT_PHRASE", "exit").lower():
            print("Exiting...")
            exit()

        print(f"User input: {user_input}")

        chat_completion: Iterator[str] = self.llm.chat_iter(user_input)

        if not self.config.get("TTS_ON", False):
            full_response = ""
            for char in chat_completion:
                full_response += char
                print(char, end="")
            return full_response

        full_response = self.speak(chat_completion)
        if self.verbose:
            print(f"\nComplete response: [\n{full_response}\n]")
        return full_response

    def get_user_input(self) -> str:
        """
        Get user input using the method specified in the configuration file.
        It can be from the console, local microphone, or the browser microphone.

        Returns:
        - str: The user input
        """
        if self.config.get("VOICE_INPUT_ON", False):
            if self.live2d and self.config.get("MIC_IN_BROWSER", False):
                # get audio from the browser microphone
                print("Listening audio from the front end...")
                audio = self.live2d.get_mic_audio()
                print("transcribing...")
                return self.asr.transcribe_np(audio)
            else:  # get audio from the local microphone
                print("Listening from the microphone...")
                return self.asr.transcribe_with_local_vad()
        else:
            return input("\n>> ")

    def speak(self, chat_completion: Iterator[str]) -> str:
        """
        Speak the chat completion using the TTS engine.

        Parameters:
        - chat_completion (Iterator[str]): The chat completion to speak

        Returns:
        - str: The full response from the LLM
        """
        full_response = ""
        if self.config.get("SAY_SENTENCE_SEPARATELY", True):
            full_response = self.speak_by_sentence_chain(chat_completion)
        else:  # say the full response at once? how stupid
            full_response = ""
            for char in chat_completion:
                print(char, end="")
                full_response += char
            print("\n")
            filename = self._generate_audio_file(full_response, "temp")

            self._play_audio_file(
                sentence=full_response,
                filepath=filename,
            )

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
            sentence = self.live2d.remove_expression_from_string(sentence)

        if sentence.strip() == "":
            return None

        return self.tts.generate_audio(sentence, file_name_no_ext=file_name_no_ext)

    def _play_audio_file(self, sentence: str, filepath: str | None) -> None:
        """
        Play the audio file either locally or remotely using the Live2D controller if available.

        Parameters:
        - sentence (str): The sentence to display
        - filepath (str): The path to the audio file. If None, no audio will be streamed.
        """

        if filepath is None:
            print("No audio to be streamed. Response is empty.")
            return

        try:
            if self.live2d:
                # Filter out expression keywords from the sentence
                expression_list = self.live2d.get_expression_list(sentence)
                if self.live2d.remove_expression_from_string(sentence).strip() == "":
                    self.live2d.send_expressions_str(sentence, send_delay=0)
                    self.live2d.send_text(sentence)
                    return
                print("streaming...")
                # Stream the audio to the frontend
                stream_audio.StreamAudio(
                    filepath,
                    display_text=sentence,
                    expression_list=expression_list,
                    base_url=self.live2d.base_url,
                ).send_audio_with_volume(wait_for_audio=True)
            else:
                if self.verbose:
                    print(f">> Playing {filepath}...")
                self.tts.play_audio_file_local(filepath)

            self.tts.remove_file(filepath, verbose=self.verbose)
        except ValueError as e:
            if str(e) == "Audio is empty or all zero.":
                print("No audio to be streamed. Response is empty.")
            else:
                raise e

    def speak_by_sentence_chain(
        self,
        chat_completion: Iterator[str],
    ) -> str:
        """
        Generate and play the chat completion sentences one by one using the TTS engine.

        Parameters:
        - chat_completion (Iterator[str]): The chat completion to speak

        Returns:
        - str: The full response from the LLM
        """

        def producer_worker(task_queue: queue):
            index = 0
            sentence_buffer = ""
            full_response = ""

            for char in chat_completion:
                if char:
                    print(char, end="")
                    sys.stdout.flush()
                    sentence_buffer += char
                    full_response += char
                    if self.is_complete_sentence(sentence_buffer):
                        # when verbose, more information is printed, so we need a new line
                        if self.verbose:
                            print("\n")
                        audio_filepath = self._generate_audio_file(
                            sentence_buffer, file_name_no_ext=f"temp-{index}"
                        )
                        audio_info = {
                            "sentence": sentence_buffer,
                            "audio_filepath": audio_filepath,
                        }
                        task_queue.put(audio_info)
                        index += 1
                        sentence_buffer = ""
            # if there is more text left in the buffer
            if sentence_buffer:  # use the same code as above to generate audio file
                print("\n")
                audio_filepath = self._generate_audio_file(
                    sentence_buffer, file_name_no_ext=f"temp-{index}"
                )
                audio_info = {
                    "sentence": sentence_buffer,
                    "audio_filepath": audio_filepath,
                }
                task_queue.put(audio_info)
                index += 1
                sentence_buffer = ""
            print("\n\n --- Audio generation completed ---")
            return full_response

        def consumer_worker(task_queue: queue):
            while True:
                audio_info = task_queue.get()
                if audio_info:
                    self._play_audio_file(
                        sentence=audio_info["sentence"],
                        filepath=audio_info["audio_filepath"],
                    )
                task_queue.task_done()

        task_queue = queue.Queue()
        threading.Thread(
            target=consumer_worker, args=(task_queue,), daemon=True
        ).start()
        full_response = producer_worker(task_queue)

        task_queue.join()

        return full_response

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


if __name__ == "__main__":
    with open("conf.yaml", "r") as f:
        config = yaml.safe_load(f)

    vtuber_main = OpenLLMVTuberMain(config)
    while True:
        vtuber_main.conversation_chain()
