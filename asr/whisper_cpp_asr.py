from pywhispercpp.model import Model

import numpy as np
from .asr_interface import ASRInterface
from .asr_with_vad import VoiceRecognitionVAD




class VoiceRecognition(ASRInterface):

    def __init__(
        self,
        model_name: str = "base",
        model_dir="asr/models",
        language: str = "en",
        print_realtime=False,
        print_progress=False, **kwargs
    ) -> None:
        
        self.model = Model(
            model=model_name,
            models_dir=model_dir,
            language=language,
            print_realtime=print_realtime,
            print_progress=print_progress,
            **kwargs
        )
        self.asr_with_vad = None
        
    def transcribe_with_local_vad(self) -> str:
        if self.asr_with_vad is None:
            self.asr_with_vad = VoiceRecognitionVAD(self.transcribe_np)
        return self.asr_with_vad.start_listening()

    def transcribe_np(self, audio: np.ndarray) -> str:
        segments = self.model.transcribe(audio, new_segment_callback=print)
        full_text = ""
        for segment in segments:
            full_text += segment.text
        return full_text

