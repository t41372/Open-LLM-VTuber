import abc
import numpy as np
from .asr_with_vad import VoiceRecognitionVAD


class ASRInterface(metaclass=abc.ABCMeta):

    asr_with_vad: VoiceRecognitionVAD = None
    SAMPLE_RATE = 16000
    NUM_CHANNELS = 1
    SAMPLE_WIDTH = 2

    # @abc.abstractmethod
    def transcribe_with_local_vad(self) -> str:
        """Activate the microphone on this device, transcribe audio when a pause in speech is detected using VAD, and return the transcription.

        This method should block until a transcription is available.

        Returns:
            The transcription of the speech audio.
        """
        if self.asr_with_vad is None:
            self.asr_with_vad = VoiceRecognitionVAD(self.transcribe_np)
        return self.asr_with_vad.start_listening()

    @abc.abstractmethod
    def transcribe_np(self, audio: np.ndarray) -> str:
        """Transcribe speech audio in numpy array format and return the transcription.

        Args:
            audio: The numpy array of the audio data to transcribe.
        """
        pass

    def nparray_to_audio_file(
        self, audio: np.ndarray, sample_rate: int, file_path: str
    ) -> None:
        """Convert a numpy array of audio data to a .wav file.

        Args:
            audio: The numpy array of audio data.
            sample_rate: The sample rate of the audio data.
            file_path: The path to save the .wav file.
        """
        import wave

        # Make sure the audio is in the range [-1, 1]
        audio = np.clip(audio, -1, 1)
        # Convert the audio to 16-bit PCM
        audio_integer = (audio * 32767).astype(np.int16)

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_integer.tobytes())
