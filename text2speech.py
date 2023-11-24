import os
import azure.cognitiveservices.speech as speechsdk
import api_keys
import traceback

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription=api_keys.TTS_API_Key, region=api_keys.TTS_REGION)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# The language of the voice that speaks.
speech_config.speech_synthesis_voice_name='en-US-AshleyNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

def test_speak():
    '''
    test the speak function
    '''
    # Get text from the console and synthesize to the default speaker.
    print("Enter some text that you want to speak >")
    speak(input())


def speak(text):
    '''
    speak the text
    text: str
        the text to speak
    '''
    # Validate text input to make sure it's a string and not empty.
    if not isinstance(text, str) or text.strip() == "":
        print("The text to speak cannot be empty or non-string.")
        print("Received type: {} and value: {}".format(type(text), text))
        traceback.print_stack()  # Print the trace stack
        return

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")

    

# test_speak()

