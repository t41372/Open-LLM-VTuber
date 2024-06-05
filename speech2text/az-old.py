import azure.cognitiveservices.speech as speechsdk
import time
import api_keys
from halo import Halo

class Speech2Text:
    def __init__(self):
        self.text = ""
        self.AZURE_API_Key = api_keys.AZURE_API_Key
        self.AZURE_REGION = api_keys.AZURE_REGION

    # This function is by default not used. It is used in the continuous speech to text service.
    def speech_recognition_callback(self, event_args, result, callbackToLLM):
        if event_args.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            result.text += event_args.result.text + " "
            print("Recognized Sentence: {}".format(event_args.result.text))
            callbackToLLM(event_args.result.text)
            
        elif event_args.result.reason == speechsdk.ResultReason.NoMatch:
            print("Nothing recognized")
        elif event_args.result.reason == speechsdk.ResultReason.EndOfDictation or event_args.result.reason == speechsdk.ResultReason.NoMatch:
            print("End of Dictation")

    # This function is by default not used. It is used in the continuous speech to text service.
    def launchContinuousSpeech2TextService(self, callbackToLLM=None):
        '''
        Launch the continuous speech to text service. The callback function will be called when a sentence is recognized.
        The speech recognizer will run continuously until the KeyboardInterrupt is raised.
        The speech recognizer will be running even if the llm is talking.
        callbackToLLM: function
            the callback function to the llm

        '''
        # set up the api key and region
        subscription_key = self.AZURE_API_Key
        region = self.AZURE_REGION

        # create the speech config and audio config
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        audio_config = speechsdk.AudioConfig(use_default_microphone=True)

        # create the speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)


        # set up the callback function
        speech_recognizer.recognizing.connect(lambda evt: print("正在识别: {}".format(evt.result.text)))
        speech_recognizer.recognized.connect(lambda evt: self.speech_recognition_callback(evt, self.result, callbackToLLM))

        # start the recognizer

        # 
        spinner = Halo(text='AI is listening...', spinner='dots')
        spinner.start()
        speech_recognizer.start_continuous_recognition()
        spinner.stop()

        try:
            # keep the program running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            pass
        finally:
            # stop the recognizer
            speech_recognizer.stop_continuous_recognition()
            print("Service Terminated. The results are:", result.text)



    def speech2TextOnce(self):
        '''
        Transcribe speech to text for one sentence.
        return: str
            the transcribed text. Return "" if nothing is recognized or failed.
        '''
        # set up the api key and region
        subscription_key = self.AZURE_API_Key
        region = self.AZURE_REGION
        
        # create the speech config
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)

        # create the speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

        # start speech recognition
        spinner = Halo(text='AI is listening...', spinner='dots')
        spinner.start()
        result = speech_recognizer.recognize_once()
        spinner.stop()

        # process recognition result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
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


    # if __name__ == "__main__":
    #     launchContinuousSpeech2TextService()


