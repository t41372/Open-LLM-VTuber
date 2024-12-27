from typing import Any

import torch
import whisper

from .asr_interface import ASRInterface


class VoiceRecognition(ASRInterface):

    def __init__(
        self,
        name: str = "base",
        download_root: str = None,
        device="cuda",
    ) -> None:
        self.model = whisper.load_model(
            name=name,
            device=device,
            download_root=download_root,
        )
        self.asr_with_vad = None

    # Implemented in asr_interface.py
    # def transcribe_with_local_vad(self) -> str: 

    def transcribe_np(self, audio: Any) -> str:

        segments = self.model.transcribe(torch.tensor(audio, dtype=torch.float32) / 32768.0)
        return segments['text']
