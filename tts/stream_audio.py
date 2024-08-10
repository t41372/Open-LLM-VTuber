from pydub import AudioSegment
from pydub.utils import make_chunks
import base64


class AudioPayloadPreparer:
    """
    A class to handle preparation of audio payloads for streaming.
    """

    def __init__(self, chunk_length_ms: int = 20):
        """
        Initializes the AudioPayloadPreparer object with constant parameters.

        Parameters:
            chunk_length_ms (int): The length of each audio chunk in milliseconds.
        """
        self.chunk_length_ms: int = chunk_length_ms

    def __get_volume_by_chunks(self, audio):
        """
        Private method to divide the audio into chunks and calculate the normalized volume (RMS) for each chunk.

        Parameters:
            audio (AudioSegment): The audio segment to process.

        Returns:
            list: Normalized volumes for each chunk.
        """
        chunks = make_chunks(audio, self.chunk_length_ms)
        volumes = [chunk.rms for chunk in chunks]
        max_volume = max(volumes)
        if max_volume == 0:
            raise ValueError("Audio is empty or all zero.")
        return [volume / max_volume for volume in volumes]

    def prepare_audio_payload(
        self, audio_path, display_text=None, expression_list=None
    ):
        """
        Prepares the audio payload for sending to a broadcast endpoint.

        Parameters:
            audio_path (str): The path to the audio file to be processed.
            display_text (str, optional): Text to be displayed with the audio.
            expression_list (list, optional): List of expressions associated with the audio.

        Returns:
            tuple: A tuple containing the prepared payload (dict) and the audio duration (float).
        """
        if not audio_path:
            raise ValueError("audio_path cannot be None or empty.")

        audio = AudioSegment.from_file(audio_path)
        audio_bytes = audio.export(format="wav").read()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        volumes = self.__get_volume_by_chunks(audio)

        payload = {
            "type": "audio",
            "audio": audio_base64,
            "volumes": volumes,
            "slice_length": self.chunk_length_ms,
            "text": display_text,
            "expressions": expression_list,
        }

        return payload, audio.duration_seconds


# Example usage:
# preparer = AudioPayloadPreparer()
# payload, duration = preparer.prepare_audio_payload("path/to/audio.mp3", display_text="Hello", expression_list=[0,1,2])
