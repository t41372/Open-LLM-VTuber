import uuid
import requests
from tts.tts_interface import TTSInterface


class TTSEngine(TTSInterface):
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8020/tts_to_audio",
        speaker_wav: str = "female",
        language: str = "en",
    ):
        self.api_url = api_url
        self.speaker_wav = speaker_wav
        self.language = language

    def generate_audio(self, text, file_name_no_ext=None):
        if file_name_no_ext is None:
            # Generate a unique filename using uuid4
            file_name = f"{uuid.uuid4()}.wav"
        else:
            file_name = file_name_no_ext

        # Prepare the data for the POST request
        data = {
            "text": text,
            "speaker_wav": self.speaker_wav,
            "language": self.language,
        }

        # Send POST request to the TTS API
        response = requests.post(self.api_url, json=data, timeout=120)

        # Check if the request was successful
        if response.status_code == 200:
            # Save the audio content to a file
            with open(file_name, "wb") as audio_file:
                audio_file.write(response.content)
            return file_name
        else:
            # Handle errors or unsuccessful requests
            print(
                f"Error: Failed to generate audio. Status code: {response.status_code}"
            )
            return None
