import pyttsx3
import sys

import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import stream_audio
import os
from pathlib import Path

# using https://github.com/thevickypedia/py3-tts because pyttsx3 is unmaintained and not working

class TTSEngine:

    def __init__(self):
        self.engine = pyttsx3.init()
        self.temp_audio_file = "temp"
        self.file_extension = "aiff"
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


    
    # deprecated, no longer used
    def speak_stream(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        [deprecated]
        Speak the text at the frontend. The audio and the data to control the mouth movement will be sent to the frontend.
        text: str
            the text to speak
        '''
        self.engine.save_to_file(text=text, filename=self.temp_audio_file)
        self.engine.runAndWait()

        stream_audio.StreamAudio(self.temp_audio_file).send_audio_with_volume(wait_for_audio=True, on_speak_start_callback=on_speak_start_callback, on_speak_end_callback=on_speak_end_callback)
        
        



        

if __name__ == "__main__": 
    TTSEngine = TTSEngine()
    TTSEngine.generate_audio("Hello, this is a test. But this is not a test. You are screwed bro. You only live once. YOLO.")