import pyttsx3

# using https://github.com/thevickypedia/py3-tts because pyttsx3 is unmaintained and not working

class TTSEngine:

    def __init__(self):
        self.engine = pyttsx3.init()

    def speak(self, text):
        '''
        speak the text
        text: str
            the text to speak
        '''
        self.engine.say(text)
        self.engine.runAndWait()

if __name__ == "__main__": 
    TTSEngine = TTSEngine()
    TTSEngine.speak("Hello, this is a test.")