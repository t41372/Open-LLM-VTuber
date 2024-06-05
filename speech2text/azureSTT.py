import azure.cognitiveservices.speech as speechsdk
from typing import Callable
import time
from halo import Halo
from dotenv import load_dotenv
import os

load_dotenv("../.env")

class SpeechToTextService:
    def __init__(self, callbackFunction: Callable = print ,subscription_key=os.getenv("AZURE_API_Key"), region=os.getenv("AZURE_REGION")):
        """
        Initializes an instance of the AzureSTT class.

        Parameters:
        - llm (Ollama): An instance of the Ollama class.
        - callbackFunction (Callable): A callback function to handle the speech-to-text results. Default is the print function.
        - subscription_key (str): The Azure API key. Default is the value of the AZURE_API_Key environment variable.
        - region (str): The Azure region. Default is the value of the AZURE_REGION environment variable.
        """
        self.subscription_key = subscription_key
        self.region = region
        self.callback = callbackFunction

    def _create_speech_recognizer(self, uses_default_microphone: bool =True):
        print("Sub: ", self.subscription_key, "Reg: ", self.region)
        # 確保 self.subscription_key 是一個字符串
        assert isinstance(self.subscription_key, str), "subscription_key must be a string"
        speech_config = speechsdk.SpeechConfig(subscription=self.subscription_key, region=self.region)
        audio_config = speechsdk.AudioConfig(use_default_microphone=uses_default_microphone)
        return speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def _speech_recognition_callback(self, event_args):
        if event_args.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            self.speech_recognizer.pause_continuous_recognition()
            print("Recognized Sentence: {}".format(event_args.result.text))
            self.callback(event_args.result.text)
            self.speech_recognizer.resume_continuous_recognition()
        elif event_args.result.reason == speechsdk.ResultReason.NoMatch:
            print("Nothing recognized")
        elif event_args.result.reason == speechsdk.ResultReason.EndOfDictation or event_args.result.reason == speechsdk.ResultReason.NoMatch:
            print("End of Dictation")

    def launch_continuous_speech_to_text_service(self):
        self.speech_recognizer = self._create_speech_recognizer(use_default_microphone=True)
        self.speech_recognizer.recognizing.connect(lambda evt: print(">> Listening: {}".format(evt.result.text)))
        self.speech_recognizer.recognized.connect(self._speech_recognition_callback)

        spinner = Halo(text='AI is listening...', spinner='dots')
        spinner.start()
        self.speech_recognizer.start_continuous_recognition()
        spinner.stop()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.speech_recognizer.stop_continuous_recognition()
            print("Service Terminated.")

    def transcribe_once(self):
        speech_recognizer = self._create_speech_recognizer()
        spinner = Halo(text='AI is listening...', spinner='dots')
        spinner.start()
        result = speech_recognizer.recognize_once()
        spinner.stop()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            self.callback(result.text)
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("Not recognized")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Recognition Canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error Info: {}".format(cancellation_details.error_details))

        print("Speech recognition end.")
        return ""
    
    def launch(self):
        """
        Continuously transcribes user speech input and processes the recognition result.

        This method runs in an infinite loop and calls the `transcribe_once` method to transcribe user speech input.
        If a recognition result is obtained, it prints the user input and calls the `callback` method to process the input.
        After processing, it prints a separator line and continues to transcribe user speech input.

        Note:
        - The `transcribe_once` method should be implemented separately.
        - The `callback` method should be implemented separately.

        Returns:
        None
        """
        while True:
            self.transcribe_once()
            # if recognitionResult != "":
            #     print("\nUser Input: \n" + recognitionResult + "\n\nAI Response: \n")
            #     self.callback(recognitionResult, self.llm)
            #     print("======\n")

if __name__ == "__main__":
    service = SpeechToTextService()
    service.launch()