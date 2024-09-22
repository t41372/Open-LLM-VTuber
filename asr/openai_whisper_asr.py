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

    def transcribe_np(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        # Whisper espera um caminho de arquivo ou bytes de áudio
        # Convertemos o array NumPy para bytes e utilizamos a função transcribe corretamente
        audio = whisper.pad_or_trim(audio)

        # Normalizar o áudio para corresponder ao formato que Whisper espera
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        # Realizar a transcrição
        result = self.model.transcribe(mel)

        # O texto transcrito está dentro da chave 'text'
        return result['text']
