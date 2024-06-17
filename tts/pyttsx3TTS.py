import pyttsx3
import sys

import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import stream_audio

# using https://github.com/thevickypedia/py3-tts because pyttsx3 is unmaintained and not working

class TTSEngine:

    def __init__(self):
        self.engine = pyttsx3.init()
        self.temp_audio_file = "temp.aiff"
        self.file_extension = "aiff"

    def speak(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        speak the text
        text: str
            the text to speak
        '''
        self.engine.say(text)
        if on_speak_start_callback is not None:
            on_speak_start_callback()
        self.engine.runAndWait()
        if on_speak_end_callback is not None:
            on_speak_end_callback()


    def generate_audio(self, text, file_name_no_ext=None, on_file_generated_callback=None):
        '''
        Generate the voice audio file using TTS.
        text: str
            the text to speak
        file_name_no_ext: str
            name of the file without extension

        
        Returns:
        str: the path to the generated audio file
        
        '''
        file_name = "temp.aiff"
        if file_name_no_ext is None:
            file_name = f"{file_name_no_ext}{self.file_extension}"
        else:
            file_name = self.temp_audio_file

        self.engine.save_to_file(text=text, filename=file_name)
        self.engine.runAndWait()
        return file_name

    def stream_audio_file(self, file_path, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        Speak the text at the frontend. The audio and the data to control the mouth movement will be sent to the frontend.
        text: str
            the text to speak
        '''

        stream_audio.StreamAudio(file_path).send_audio_with_volume(wait_for_audio=True, on_speak_start_callback=on_speak_start_callback, on_speak_end_callback=on_speak_end_callback)
    
    def speak_stream(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
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