# Original code by David Ng in [GlaDOS](https://github.com/dnhkng/GlaDOS), licensed under the MIT License
# https://opensource.org/licenses/MIT#
# Modifications by Yi-Ting Chiu as part of OpenLLM-VTuber, licensed under the MIT License
# https://opensource.org/licenses/MIT
#
#
from .asr_interface import ASRInterface
from scipy.io.wavfile import write
import numpy as np
from faster_whisper import WhisperModel
from .asr_with_vad import VoiceRecognitionVAD


class VoiceRecognition(ASRInterface):
    """Wrapper around Faster Whisper, which is a CTranslate2 implementation of the Whisper
    speech recognition model.

    This class is not thread-safe, so you should only use it from one thread.

    Args:
        model: The path to the model file to use.
    """

    BEAM_SEARCH = True
    SAMPLE_RATE = 16000  # Sample rate for input stream

    def __init__(
        self,
        model_path: str = "distil-medium.en",
        language: str = "en",
        device: str = "auto",
    ) -> None:
        self.MODEL_PATH = model_path
        self.LANG = language

        self.model = WhisperModel(model_path, device=device, compute_type="float32")
        self.asr_with_vad = None

    def transcribe_with_local_vad(self) -> str:
        """Transcribe audio using the given parameters."""
        if self.asr_with_vad is None:
            self.asr_with_vad = VoiceRecognitionVAD(self.transcribe_np)
        return self.asr_with_vad.start_listening()

    def transcribe_np(self, audio: np.ndarray) -> str:

        segments, info = self.model.transcribe(
            audio,
            beam_size=5 if self.BEAM_SEARCH else 1,
            language=self.LANG,
            condition_on_previous_text=False,
        )

        text = [segment.text for segment in segments]

        if not text:
            return ""
        else:
            return "".join(text)
