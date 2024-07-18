import os
import sys
from pathlib import Path

import pyttsx3

from .tts_interface import TTSInterface

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


# using https://github.com/thevickypedia/py3-tts because pyttsx3 is unmaintained and not working

class TTSEngine(TTSInterface):

    def __init__(self):
        self.engine = pyttsx3.init()
        self.temp_audio_file = "temp"
        self.file_extension = "aiff"
        self.new_audio_dir = "./cache"

        if not os.path.exists(self.new_audio_dir):
            os.makedirs(self.new_audio_dir)

    def speak_local(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        Speak the text on the speaker.

        text: str
            the text to speak
        on_speak_start_callback: function
            the callback function to call when synthesis starts
        on_speak_end_callback: function
            the callback function to call when synthesis ends
        '''
        self.engine.say(text)
        if on_speak_start_callback is not None:
            on_speak_start_callback()
        self.engine.runAndWait()
        if on_speak_end_callback is not None:
            on_speak_end_callback()


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



        self.engine.save_to_file(text=text, filename=file_name)
        self.engine.runAndWait()
        return file_name

       



        

if __name__ == "__main__": 
    TTSEngine = TTSEngine()
    TTSEngine.generate_audio("Hello, this is a test. But this is not a test. You are screwed bro. You only live once. YOLO.")