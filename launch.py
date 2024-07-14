import os
from typing import Iterator
import concurrent.futures
import asyncio
import yaml
from live2d import Live2dController
from tts.tts_factory import TTSFactory
from tts.tts_interface import TTSInterface
from llm.llm_factory import LLMFactory
from llm.llm_interface import LLMInterface
from asr.asr_factory import ASRFactory
from asr.asr_interface import ASRInterface
from tts import stream_audio
from prompts import prompt_loader


class OpenLLMVTuberMain:

    config: dict
    llm: LLMInterface
    asr: ASRInterface
    tts: TTSInterface
    live2d: Live2dController

    def __init__(self, config: dict):
        self.config = config
        self.live2d = self.init_live2d()
        self.llm = self.init_llm()
        self.asr = self.init_asr() if self.config.get("VOICE_INPUT_ON", False) else None
        self.tts = self.init_tts() if self.config.get("TTS_ON", False) else None

    def init_live2d(self):
        live2d_on = self.config.get("LIVE2D", False)
        if live2d_on:
            live2d_model = self.config.get("LIVE2D_MODEL")
            url = f"{self.config.get('PROTOCOL', 'http://')}{self.config.get('HOST', 'localhost')}:{self.config.get('PORT', 8000)}"
            live2d_controller = Live2dController(live2d_model, base_url=url)
            return live2d_controller
        return None

    def init_llm(self):
        llm_provider = self.config.get("LLM_PROVIDER")
        llm_config = self.config.get(llm_provider, {})
        system_prompt = self.get_system_prompt()

        llm = LLMFactory.create_llm(
            llm_provider=llm_provider, SYSTEM_PROMPT=system_prompt, **llm_config
        )
        return llm

    def init_asr(self):
        asr_model = self.config.get("ASR_MODEL")
        asr_config = self.config.get(asr_model, {})
        if asr_model == "AzureSTT":
            import api_keys

            asr_config = {
                "callback": print,
                "subscription_key": api_keys.AZURE_API_Key,
                "region": api_keys.AZURE_REGION,
            }

        asr = ASRFactory.get_asr_system(asr_model, **asr_config)
        return asr

    def init_tts(self):
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

    def get_system_prompt(self):
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

        if self.config.get("VERBOSE", False):
            print("\n === System Prompt ===")
            print(system_prompt)

        return system_prompt

    def conversation_chain(self) -> str:
        """
        One iteration of the main conversation.
        1. Get user input
        2. Call the LLM with the user input
        3. Speak
        """

        user_input = self.get_user_input()
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
        print(f"\nFull response: {full_response}")

    def get_user_input(self):
        """
        Get user input using the method specified in the configuration file.
        It can be from the console, local microphone, or the browser microphone.

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

    def speak(self, chat_completion: Iterator[str]):

        full_response = ""
        if self.config.get("SAY_SENTENCE_SEPARATELY", True):
            full_response = asyncio.run(self.speak_by_sentence_chain(chat_completion))
        else:  # say the full response at once? how stupid
            full_response = ""
            for char in chat_completion:
                print(char, end="")
                full_response += char
            print("\n")
            filename = asyncio.run(self._generate_audio_file(full_response, "temp"))
            
            asyncio.run(
                self._play_audio_file(
                    sentence=full_response,
                    filename=filename,
                )
            )

        return full_response

    async def _generate_audio_file(self, sentence, file_name_no_ext):
        print("generate...")

        if not self.tts:
            return None

        if self.live2d:
            sentence = self.live2d.remove_expression_from_string(sentence)

        if sentence.strip() == "":
            return None

        return await asyncio.to_thread(
            self.tts.generate_audio, sentence, file_name_no_ext=file_name_no_ext
        )

    async def _play_audio_file(self, sentence, filename):
        print("stream...")

        if not self.live2d:
            await asyncio.to_thread(self.tts.speak_local, sentence)
            return

        if filename is None:
            print("No audio to be streamed. Response is empty.")
            return

        expression_list = self.live2d.get_expression_list(sentence)

        if self.live2d.remove_expression_from_string(sentence).strip() == "":
            self.live2d.send_expressions_str(sentence, send_delay=0)
            self.live2d.send_text(sentence)
            return

        try:
            # todo: refactor stream_audio to a real async coroutine later
            await asyncio.to_thread(
                stream_audio.StreamAudio(
                    filename,
                    display_text=sentence,
                    expression_list=expression_list,
                    base_url=self.live2d.base_url,
                ).send_audio_with_volume, wait_for_audio=True
            )

            if os.path.exists(filename):
                os.remove(filename)
                print(f"File {filename} removed successfully.")
            else:
                print(f"File {filename} does not exist.")
        except ValueError as e:
            if str(e) == "Audio is empty or all zero.":
                print("No audio to be streamed. Response is empty.")
            else:
                raise e

    async def speak_by_sentence_chain(
        self,
        chat_completion: Iterator[str],
    ):

        async def producer_worker(queue):
            index = 0
            sentence_buffer = ""
            full_response = ""

            for char in chat_completion:
                if char:
                    print(char, end="")
                    sentence_buffer += char
                    full_response += char
                    if self.is_complete_sentence(sentence_buffer):
                        print("\n")
                        audio_filepath = await self._generate_audio_file(
                            sentence_buffer, file_name_no_ext=f"temp-{index}"
                        )
                        audio_info = {
                            "sentence": sentence_buffer,
                            "audio_filepath": audio_filepath,
                        }
                        await queue.put(audio_info)
                        index += 1
                        sentence_buffer = ""
            # if there is more text left in the buffer
            if sentence_buffer: # use the same code as above to generate audio file
                print("\n")
                audio_filepath = await self._generate_audio_file(
                    sentence_buffer, file_name_no_ext=f"temp-{index}"
                )
                audio_info = {
                    "sentence": sentence_buffer,
                    "audio_filepath": audio_filepath,
                }
                await queue.put(audio_info)
                index += 1
                sentence_buffer = ""
            print("\nAudio generation completed.")
            return full_response

        async def consumer_worker(queue: asyncio.Queue):
            while True:
                audio_info = await queue.get()
                if audio_info:
                    await self._play_audio_file(
                        audio_info["sentence"], audio_info["audio_filepath"]
                    )
                queue.task_done()

        queue = asyncio.Queue()
        producer_task = asyncio.create_task(producer_worker(queue))
        consumer_task = asyncio.create_task(consumer_worker(queue))
        full_response = await producer_task
        await queue.join()
        consumer_task.cancel()

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
