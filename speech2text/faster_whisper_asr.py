# Original code by David Ng in [GlaDOS](https://github.com/dnhkng/GlaDOS), licensed under the MIT License
# https://opensource.org/licenses/MIT# 
# Modifications by Yi-Ting Chiu as part of OpenLLM-VTuber, licensed under the MIT License
# https://opensource.org/licenses/MIT
# 
#

from scipy.io.wavfile import write
import numpy as np
from faster_whisper import WhisperModel
from speech2text.asr_with_vad import VoiceRecognitionVAD

LANG = "en"
WORD_LEVEL_TIMINGS = False
BEAM_SEARCH = True
MODEL_PATH = "distil-medium.en"
SAMPLE_RATE = 16000  # Sample rate for input stream


class VoiceRecognition:
    """Wrapper around Faster Whisper, which is a CTranslate2 implementation of the Whisper
    speech recognition model.

    This class is not thread-safe, so you should only use it from one thread.

    Args:
        model: The path to the model file to use.
    """

    def __init__(self, model_path: str = MODEL_PATH) -> None:
        self.model = WhisperModel(model_path, device="auto", compute_type="float32")
        self.asr_with_vad = VoiceRecognitionVAD(self.transcribe_np)

    def transcribe_with_vad(self) -> str:
        """Transcribe audio using the given parameters."""
        return self.asr_with_vad.start_listening()


    def transcribe_np(self, audio: np.ndarray) -> str:
        """Transcribe audio using the given parameters.

        Args:
            audio: The numpy array of the audio data to transcribe.
        """

        # Run the model
        # segments, info = self.model.transcribe(audio, beam_size=5 if BEAM_SEARCH else 1, language=LANG)
        
        segments, info = self.model.transcribe(audio, beam_size=5 if BEAM_SEARCH else 1, language="en", condition_on_previous_text=False)

        # Get the text
        text = [segment.text for segment in segments]

        if not text:
            return ""
        else:
            return "".join(text)