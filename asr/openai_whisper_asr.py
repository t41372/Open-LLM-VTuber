import numpy as np
import whisper
from .asr_interface import ASRInterface
from .asr_with_vad import VoiceRecognitionVAD





class VoiceRecognition(ASRInterface):

    def __init__(
        self,
        name: str = "base",
        download_root: str = None,
        device="cpu",
    ) -> None:
        self.model = whisper.load_model(
            name=name,
            device=device,
            download_root=download_root,
        )
        self.asr_with_vad = None

    def transcribe_with_local_vad(self) -> str:
        if self.asr_with_vad is None:
            self.asr_with_vad = VoiceRecognitionVAD(self.transcribe_np)
        return self.asr_with_vad.start_listening()
    
    def transcribe_np(self, audio: np.ndarray) -> str:
        segments = self.model.transcribe(audio)
        full_text = ""
        for segment in segments:
            full_text += segment
        return full_text
