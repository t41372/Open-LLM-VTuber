from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
import sounddevice as sd
import soundfile as sf


import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import stream_audio
from pathlib import Path


import time
import platform

if platform.system() == "Darwin":
    print(">> Note: Running barkTTS on macOS can be very slow.")
    os.environ["SUNO_ENABLE_MPS"] = "True"
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    os.environ["SUNO_OFFLOAD_CPU"] = "False"


class TTSEngine:

    def __init__(self):
        # download and load all models
        preload_models()
        self.voice = "v2/en_speaker_1"

        self.temp_audio_file = "temp"
        self.file_extension = "wav"
        self.new_audio_dir = "./cache"

        if not os.path.exists(self.new_audio_dir):
            os.makedirs(self.new_audio_dir)


    def speak(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        Speak the text on the speaker.

        text: str
            the text to speak
        on_speak_start_callback: function
            the callback function to call when synthesis starts
        on_speak_end_callback: function
            the callback function to call when synthesis ends
        '''
        filepath = self.generate_audio(text)
        if on_speak_start_callback is not None:
            on_speak_start_callback()
        data, fs = sf.read(filepath, dtype='float32')  
        # 使用 sounddevice 播放音頻數據
        sd.play(data, fs)
        # 等待音頻播放完成
        sd.wait()
        if on_speak_end_callback is not None:
            on_speak_end_callback()
        self.__remove_file(filepath)


    def generate_audio(self, text, file_name_no_ext=None):
        '''
        Generate speech audio file using TTS.
        text: str
            the text to speak
        file_name_no_ext: str
            name of the file without extension

        
        Returns:
        str: the path to the generated audio file
        
        '''

        file_name = self.__format_filename(file_name_no_ext)

        start_time = time.time()

        # generate audio from text
        audio_array = generate_audio(text, history_prompt=self.voice)

        # save audio to disk
        write_wav(filename=file_name, rate=SAMPLE_RATE, data=audio_array)

        end_time = time.time()
        execution_time = end_time - start_time
        print("Execution time:", execution_time, "seconds", "\n", execution_time/60, "minutes")

        return file_name


    def __format_filename(self, file_name_no_ext=None):
        file_name = "temp"
        if file_name_no_ext is None:
            file_name = self.temp_audio_file
        else:
            file_name = file_name_no_ext
        
        file_name = str(Path(self.new_audio_dir) / f"{file_name}.{self.file_extension}")

        return file_name

    def stream_audio_file(self, file_path, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        Stream the audio file to the frontend and wait for the audio to finish. The audio and the data to control the mouth movement will be sent to the live2d frontend.
        
        file_path: str
            the path of the audio file to stream
        on_speak_start_callback: function
            A callback function to be called at the start of the audio playback.
        on_speak_end_callback: function
            A callback function to be called at the end of the audio playback.
        '''

        stream_audio.StreamAudio(file_path).send_audio_with_volume(wait_for_audio=True, on_speak_start_callback=on_speak_start_callback, on_speak_end_callback=on_speak_end_callback)

        self.__remove_file(file_path)

    def __remove_file(self, file_path):
        '''
        Remove the file at the specified file path.
        file_path: str
            the path of the file to be removed
        '''
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} removed successfully.")
        else:
            print(f"File {file_path} does not exist.")




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
    print("Execution time:", execution_time, "seconds", "\n", execution_time/60, "minutes")



