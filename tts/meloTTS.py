import os
import sys
from pathlib import Path
import soundfile as sf

from melo.api import TTS

from .tts_interface import TTSInterface

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)




class TTSEngine(TTSInterface):

    def __init__(
        self,
        speaker: str = "EN-Default",
        language: str = "EN",
        device: str = "auto",
        speed: float = 1.0,
    ):
        # Speed is adjustable
        self.speed = speed

        # CPU is sufficient for real-time inference.
        # You can set it manually to 'cpu' or 'cuda' or 'cuda:0' or 'mps'

        # English
        self.model = TTS(language=language, device=device)
        self.speaker_id = self.model.hps.data.spk2id[speaker]

        self.temp_audio_file = "temp"
        self.file_extension = "wav"
        self.new_audio_dir = "./cache"

        if not os.path.exists(self.new_audio_dir):
            os.makedirs(self.new_audio_dir)



    def generate_audio(self, text, file_name_no_ext=None):
        """
        Generate speech audio file using TTS.
        text: str
            the text to speak
        file_name_no_ext: str
            name of the file without extension


        Returns:
        str: the path to the generated audio file

        """

        file_name = "temp"
        if file_name_no_ext is None:
            file_name = self.temp_audio_file
        else:
            file_name = file_name_no_ext

        file_name = str(Path(self.new_audio_dir) / f"{file_name}.{self.file_extension}")

        # Default accent
        self.model.tts_to_file(text, self.speaker_id, f"{file_name}", speed=self.speed)

        return file_name
