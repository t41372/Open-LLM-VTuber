import os
import yaml
from live2d import Live2dController
from tts.tts_factory import TTSFactory
from llm.llm_factory import LLMFactory
from asr.asr_factory import ASRFactory
from tts import stream_audio
from prompts import prompt_loader


class OpenLLMVTuberMain:
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

    def conversation_loop(self):
        exit_phrase = self.config.get("EXIT_PHRASE", "exit").lower()
        voice_input_on = self.config.get("VOICE_INPUT_ON", False)

        while True:
            user_input = ""
            if self.live2d and self.config.get("MIC_IN_BROWSER", False):
                print("Listening from the front end...")
                audio = self.live2d.get_mic_audio()
                print("transcribing...")
                user_input = self.asr.transcribe_np(audio)
            elif voice_input_on:
                user_input = self.asr.transcribe_with_local_vad()
            else:
                user_input = input(">> ")

            if user_input.strip().lower() == exit_phrase:
                print("Exiting...")
                break
            print(f"User input: {user_input}")
            self.call_llm(user_input)

    def call_llm(self, text):
        if not self.config.get("TTS_ON", False):
            self.llm.chat(text)
            return

        def generate_audio_file(sentence, file_name_no_ext):
            print("generate...")

            if not self.tts:
                return None

            if self.live2d:
                sentence = self.live2d.remove_expression_from_string(sentence)

            if sentence.strip() == "":
                return None

            return self.tts.generate_audio(sentence, file_name_no_ext=file_name_no_ext)

        def stream_audio_file(sentence, filename):
            print("stream...")

            if not self.live2d:
                self.tts.speak_local(sentence)
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
                stream_audio.StreamAudio(
                    filename,
                    display_text=sentence,
                    expression_list=expression_list,
                    base_url=self.live2d.base_url,
                ).send_audio_with_volume(wait_for_audio=True)

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

        if self.config.get("SAY_SENTENCE_SEPARATELY", False):
            result = self.llm.chat_stream_audio(
                text,
                generate_audio_file=generate_audio_file,
                stream_audio_file=stream_audio_file,
            )
        else:
            result = self.llm.chat_stream_audio(text)
            stream_audio_file(result, generate_audio_file(result, "temp"))


if __name__ == "__main__":
    with open("conf.yaml", "r") as f:
        config = yaml.safe_load(f)

    vtuber_main = OpenLLMVTuberMain(config)
    vtuber_main.conversation_loop()
