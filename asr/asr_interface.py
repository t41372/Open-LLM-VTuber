import abc
import numpy as np

class ASRInterface(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def transcribe_with_local_vad(self) -> str:
        """Activate the microphone on this device, transcribe audio when a pause in speech is detected using VAD, and return the transcription.
        
        This method should block until a transcription is available.
        
        Returns:
            The transcription of the speech audio.
            """
        pass
    
    @abc.abstractmethod
    def transcribe_np(self, audio: np.ndarray) -> str:
        """Transcribe speech audio in numpy array format and return the transcription.

        Args:
            audio: The numpy array of the audio data to transcribe.
        """
        pass

