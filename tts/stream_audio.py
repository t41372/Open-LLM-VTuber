from pydub import AudioSegment
from pydub.utils import make_chunks
import time
import threading

import requests
import json as JSON
import base64

class StreamAudio:
    """
    A class to handle streaming audio files, including sending audio data to a broadcast endpoint.
    """

    def __init__(self, audio_path, display_text=None, expression_list=None):
        """
        Initializes the StreamAudio object with the specified audio file path.

        Parameters:
            audio_path (str): The path to the audio file to be streamed.
        """
        if not audio_path:
            raise ValueError("audio_path cannot be None or empty.")
        
        self.display_text = display_text
        self.expression_list = expression_list

        self.audio_path = audio_path
        self.previous_time = 0
        self.wf = None
        self.maxNum = 0
        
        self.volumes = []
        self.chunk_length_ms = 20
        self.audio = AudioSegment.from_file(self.audio_path)
        self.__getVolumeByChunks()
    

    def __getVolumeByChunks(self):
        """
        Private method to divide the audio into chunks, calculate the volume (RMS) for each chunk, and normalize these volumes.
        """
        
        chunks = make_chunks(self.audio, self.chunk_length_ms)
        self.volumes = [chunk.rms for chunk in chunks]
        self.maxNum = max(self.volumes)
        self.volumes = [volume/self.maxNum for volume in self.volumes]



    def send_audio_with_volume(self, wait_for_audio=True, on_speak_start_callback=None, on_speak_end_callback=None):
        """
        Sends the audio data along with volume information to a broadcast endpoint. Optionally triggers callbacks
        at the start and end of the speaking.

        wait_for_audio (bool): 
            If True, waits for the length of the audio before proceeding. Default is True.
        on_speak_start_callback (callable, optional): 
            A callback function to be called at the start of the audio playback.
        on_speak_end_callback (callable, optional): 
            A callback function to be called at the end of the audio playback.
        """
        audio_bytes = self.audio.export(format='wav').read()

        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        self.send_audio_to_broadcast(audio_base64)
        if callable(on_speak_start_callback):
            threading.Thread(target=on_speak_start_callback).start()

        if wait_for_audio:
            self.sleep_for_audio_length()
        if callable(on_speak_end_callback):
            on_speak_end_callback()



    def sleep_for_audio_length(self):
        """
        Wait for the front end to finish playing the audio before proceeding.
        """
        audio_length = self.audio.duration_seconds
        time.sleep(audio_length)
    


    def send_audio_to_broadcast(self, audio_base64):
        """
        Sends the base64 encoded audio data along with volume information to a predefined broadcast URL.

        Parameters:
            audio_base64 (str): The base64 encoded string of the audio data.
        """

        url = "http://127.0.0.1:8000/broadcast"

        payload = {
            "type" : "audio", 
            "audio": audio_base64,
            "volumes": self.volumes,
            "slice_length": self.chunk_length_ms,
            "text": self.display_text,
            "expressions": self.expression_list}


        data = {"message": JSON.dumps(payload)}
        response = requests.post(url, json=data)

        # print(f"Response Status Code: {response.status_code}")
        if not response.ok:
            print("Failed to send audio to the broadcast route.")


if __name__ == "__main__":
    audio_path = "../cache/temp-8.mp3"
    stream_audio = StreamAudio(audio_path, display_text="YEESSSSS[fun!]", expression_list=[0,2,3,2]).send_audio_with_volume()
    input("end")