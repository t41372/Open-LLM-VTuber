
import os
import yaml


from live2d import Live2dController
from tts.tts_factory import TTSFactory
from llm.llm_factory import LLMFactory
from asr.asr_factory import ASRFactory
from tts import stream_audio
from prompts import prompt_loader


config = {}
with open("conf.yaml", "r") as f:
    config = yaml.safe_load(f)



def get_config(key, default=None):
    return config.get(key, default)



# initialize live2d
def init_live2d():
    live2d_on = get_config("LIVE2D", False)
    if live2d_on:
        live2d_model = get_config("LIVE2D_MODEL")

        url = f"{get_config('PROTOCOL', 'http://')}{get_config('HOST', 'localhost')}:{get_config('PORT', 8000)}"
        live2d_controller = Live2dController(live2d_model, base_url=url)
        return live2d_controller
    return None


live2d = init_live2d()


def init_llm():

    llm_provider = get_config("LLM_PROVIDER")
    llm_config = get_config(llm_provider, {})

    llm = LLMFactory.create_llm(
        llm_provider=llm_provider, SYSTEM_PROMPT=system_prompt, **llm_config
    )

    return llm


# Initialize speech recognition and speech synthesis services
def init_speech_services():
    voice_input_on = get_config("VOICE_INPUT_ON", False)
    tts_on = get_config("TTS_ON", False)
    speech2text, tts = None, None

    if voice_input_on:
        asr_model = get_config("STT_MODEL")

        asr_config = {}

        if asr_model == "AzureSTT":
            import api_keys

            asr_config = {
                "callback": print,
                "subscription_key": api_keys.AZURE_API_Key,
                "region": api_keys.AZURE_REGION,
            }
        else:
            asr_config = get_config(asr_model, {})

        speech2text = ASRFactory.get_asr_system(asr_model, **asr_config)

    if tts_on:
        tts_model = get_config("TTS_MODEL", "pyttsx3TTS")

        if tts_model == "AzureTTS":
            import api_keys

            tts_config = {
                "api_key": api_keys.AZURE_API_Key,
                "region": api_keys.AZURE_REGION,
                "voice": api_keys.AZURE_VOICE,
            }
        else:
            tts_config = get_config(tts_model, {})

        tts = TTSFactory.get_tts_engine(tts_model, **tts_config)

    return speech2text, tts


# Interaction modes
def conversation_loop(llm, speech2text, tts):
    exit_phrase = get_config("EXIT_PHRASE", "exit").lower()
    voice_input_on = get_config("VOICE_INPUT_ON", False)

    while True:

        user_input = ""
        if live2d and get_config("MIC_IN_BROWSER", False):
            print("Listening from the front end...")
            audio = live2d.get_mic_audio()
            print("transcribing...")
            user_input = speech2text.transcribe_np(audio)
        elif voice_input_on:
            user_input = speech2text.transcribe_with_local_vad()
        else:
            user_input = input(">> ")

        if user_input.strip().lower() == exit_phrase:
            print("Exiting...")
            break
        print(f"User input: {user_input}")
        call_llm(user_input, llm, tts)


def call_llm(text, llm, tts):

    if not get_config("TTS_ON", False):
        llm.chat(text)
        return

    # Prepare callback functions for generating and streaming audio
    def generate_audio_file(sentence, file_name_no_ext):
        """
        Generate audio file from the given sentence.
        sentence: str
            the sentence to generate audio from
        file_name_no_ext: str
            name of the file without extension

            Returns:
            str: the path to the generated audio file.
            None if TTS is off or the sentence is empty.
        """

        print("generate...")

        if not get_config("TTS_ON", False):
            return None

        if live2d:
            sentence = live2d.remove_expression_from_string(sentence)

        if sentence.strip() == "":
            return None

        return tts.generate_audio(sentence, file_name_no_ext=file_name_no_ext)

    def stream_audio_file(sentence, filename):
        """
        Stream the audio file to the frontend and wait for the audio to finish. The audio and the data to control the mouth movement will be sent to the live2d frontend.

        sentence: str
            the sentence to speak
        filename: str
            the path of the audio file to stream
        """
        print("stream...")

        if not live2d:
            tts.speak_local(sentence)
            return

        if filename is None:
            print("No audio to be streamed. Response is empty.")
            return

        expression_list = live2d.get_expression_list(sentence)

        if live2d.remove_expression_from_string(sentence).strip() == "":
            live2d.send_expressions_str(sentence, send_delay=0)
            live2d.send_text(sentence)
            return

        try:
            stream_audio.StreamAudio(
                filename,
                display_text=sentence,
                expression_list=expression_list,
                base_url=live2d.base_url,
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

    if get_config("SAY_SENTENCE_SEPARATELY", False):
        result = llm.chat_stream_audio(
            text,
            generate_audio_file=generate_audio_file,
            stream_audio_file=stream_audio_file,
        )
    else:
        result = llm.chat_stream_audio(text)
        stream_audio_file(result, generate_audio_file(result, "temp"))


if __name__ == "__main__":

    try:

        if get_config("PERSONA_CHOICE"):
            system_prompt = prompt_loader.load_persona(get_config("PERSONA_CHOICE"))
        else:
            system_prompt = get_config("DEFAULT_PERSONA_PROMPT_IN_YAML")

        if get_config("LIVE2D"):
            system_prompt += prompt_loader.load_util(
                get_config("LIVE2D_Expression_Prompt")
            ).replace("[<insert_emomap_keys>]", live2d.getEmoMapKeyAsString())

        if get_config("VERBOSE", default=False):
            print("\n === System Prompt ===")
            print(system_prompt)

        llm = init_llm()

        speech2text, tts = init_speech_services()
        conversation_loop(llm, speech2text, tts)
    except Exception as e:
        print(f"Error initializing: {e}")
        raise
        # sys.exit(1)
