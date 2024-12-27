import os
import sys
from pathlib import Path
import time
import platform
from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from .tts_interface import TTSInterface

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


class TTSEngine(TTSInterface):

    def __init__(self, voice="v2/en_speaker_1"):

        if platform.system() == "Darwin":
            print(">> Note: Running barkTTS on macOS can be very slow.")
            os.environ["SUNO_ENABLE_MPS"] = "True"
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            os.environ["SUNO_OFFLOAD_CPU"] = "False"

        # download and load all models
        preload_models()
        self.voice = voice

        self.temp_audio_file = "temp"
        self.file_extension = "wav"
        self.new_audio_dir = "cache"

        if not os.path.exists(self.new_audio_dir):
            os.makedirs(self.new_audio_dir)

    def generate_audio(self, text, file_name_no_ext=None):
        """
        Generate speech audio file using TTS.
        text: str
            the text to speak
        file_name_no_ext: str
            name of the file without extension


        Returns:
        str: the path to the generated audio file

        """

        file_name = self.generate_cache_file_name(file_name_no_ext, self.file_extension)

        start_time = time.time()

        # generate audio from text
        audio_array = generate_audio(text, history_prompt=self.voice)

        # save audio to disk
        write_wav(filename=file_name, rate=SAMPLE_RATE, data=audio_array)

        end_time = time.time()
        execution_time = end_time - start_time
        print(
            "Execution time:",
            execution_time,
            "seconds",
            "\n",
            execution_time / 60,
            "minutes",
        )

        return file_name


def sample():
    # download and load all models
    preload_models()

    start_time = time.time()

    # generate audio from text
    text_prompt = """
        Hello, my name is Suuuuuuunooooooo!! And, uh — and I like pizza. [laughs] 
        But I also have other interests such as playing tic tac toe. This is not my first time playing tic tac toe, but I absolutely hate it.
    """
    audio_array = generate_audio(text_prompt, history_prompt="v2/en_speaker_1")

    # save audio to disk
    write_wav("bark_generation.wav", SAMPLE_RATE, audio_array)

    end_time = time.time()
    execution_time = end_time - start_time
    print(
        "Execution time:",
        execution_time,
        "seconds",
        "\n",
        execution_time / 60,
        "minutes",
    )
