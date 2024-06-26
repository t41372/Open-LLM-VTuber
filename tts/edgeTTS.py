import edge_tts

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import os
from pathlib import Path

import sounddevice as sd
import soundfile as sf

# Check out doc at https://github.com/rany2/edge-tts
# Use `edge-tts --list-voices` to list all available voices

DEFAULT_VOICE = "en-US-AvaMultilingualNeural"

class TTSEngine:

    def __init__(self, voice=DEFAULT_VOICE):
        self.voice = voice

        self.temp_audio_file = "temp"
        self.file_extension = "mp3"
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
        file_name = "temp"
        if file_name_no_ext is None:
            file_name = self.temp_audio_file
        else:
            file_name = file_name_no_ext
        
        file_name = str(Path(self.new_audio_dir) / f"{file_name}.{self.file_extension}")

        communicate = edge_tts.Communicate(text, self.voice)
        communicate.save_sync(file_name)

        return file_name

    

if __name__ == "__main__":
    tts = TTSEngine()
    tts.speak("Hello World! You no, this is a very interesting phenomenoooooon that somebody is reading this stupid code", lambda: print(">> Start"), lambda: print(">> End"))


# en-US-AvaMultilingualNeural
# en-US-EmmaMultilingualNeural
# en-US-JennyNeural