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


    def __speak_file(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        speak the text by generate the audio file first and then play it, which is different from speak()
        text: str
            the text to speak
        '''
        self.engine.save_to_file(text=text, filename=self.temp_audio_file)
        self.engine.runAndWait()

    
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
    TTSEngine.__speak_file("Hello, this is a test. But this is not a test. You are screwed bro. You only live once. YOLO.")