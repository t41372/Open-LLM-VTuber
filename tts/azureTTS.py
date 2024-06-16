import azure.cognitiveservices.speech as speechsdk

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import stream_audio



class TTSEngine:

    def __init__(self, sub_key, region, voice):
        '''
        Initialize the Azure Text-to-Speech service
        api_key: str
            the Azure API key. Default is the value in api_keys.py
        region: str
            the Azure region. Default is the value in api_keys.py
        voice: str
            the voice to use. Default is the value in api_keys.py
        '''
        # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
        self.speech_config = speechsdk.SpeechConfig(subscription=sub_key, region=region)
        # The language of the voice that speaks.
        self.speech_config.speech_synthesis_voice_name=voice

        self.temp_audio_file = "temp.wav"

        self.speakerAudioConfig = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        self.fileAudioConfig = speechsdk.audio.AudioOutputConfig(filename=self.temp_audio_file)
        

        

        

    def speak(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        speak the text to the speaker
        text: str
            the text to speak
        on_speak_start_callback: function
            the callback function to call when synthesis starts
        on_speak_end_callback: function
            the callback function to call when synthesis ends
        '''
        return self.__speak_with_audio_config(text, 
                            audio_config=self.speakerAudioConfig, 
                            on_speak_start_callback=on_speak_start_callback, 
                            on_speak_end_callback=on_speak_end_callback)
    
    def __speak_file(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        speak the text by generate the audio file first and then play it, which is different from speak()
        text: str
            the text to speak
        on_speak_start_callback: function
            the callback function to call when synthesis starts
        on_speak_end_callback: function
            the callback function to call when synthesis ends
        '''
        return self.__speak_with_audio_config(text, 
                            audio_config=self.fileAudioConfig, 
                            on_speak_start_callback=on_speak_start_callback, 
                            on_speak_end_callback=on_speak_end_callback)

    def __speak_with_audio_config(self, text, audio_config, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        speak the text with specified audio configuration
        text: str
            the text to speak
        audio_config: speechsdk.audio.AudioOutputConfig
            the audio configuration to use
        on_speak_start_callback: function
            the callback function to call when synthesis starts
        on_speak_end_callback: function
            the callback function to call when synthesis ends
        '''
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, 
                                                         audio_config=audio_config)

        # check if the text is empty or not a string
        if not isinstance(text, str):
            print("AzureTTS: The text cannot be non-string.")
            print("Received type: {} and value: {}".format(type(text), text))
            return
        text = text.strip()
        
        if text.strip() == "":
            print("AzureTTS: There is no text to speak.")
            print(f"Received text: {text}")
            return

        # speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
        if on_speak_start_callback is not None:
            on_speak_start_callback()
        
        speech_synthesis_result = speech_synthesizer.speak_text(text)
        
        if on_speak_end_callback is not None:
            on_speak_end_callback()
        

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            if on_speak_end_callback is not None:
                on_speak_end_callback()
            print(">> Speech synthesized for text [{}]".format(text))
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")

    def speak_stream(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        Speak the text at the frontend. The audio and the data to control the mouth movement will be sent to the frontend.
        text: str
            the text to speak
        '''
        # the callback should not be called here, because the audio is not played here
        self.__speak_file(text, on_speak_start_callback=None, on_speak_end_callback=None)

        stream_audio.StreamAudio(self.temp_audio_file).send_audio_with_volume(wait_for_audio=True, on_speak_start_callback=on_speak_start_callback, on_speak_end_callback=on_speak_end_callback)
        

    # test_speak()







if __name__ == "__main__":
    tts = TTSEngine(input("Enter the Azure API key: "), input("Enter the Azure region: "), input("Enter the voice: "))
    tts.speak("Testing, testing... finne.", 
              on_speak_start_callback=lambda: print("<<Synthesis started.>>"), 
              on_speak_end_callback=lambda: print("<<Synthesis ended.>>"))
    # tts.speak("I am fine, thank you.")
    # tts.speak("Goodbye!")



