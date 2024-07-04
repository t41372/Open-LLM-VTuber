from typing import Type
from .asr_interface import ASRInterface
from .faster_whisper_asr import VoiceRecognition as FasterWhisperASR
from .azure_asr import VoiceRecognition as AzureASR


class ASRFactory:
    @staticmethod
    def get_asr_system(system_name: str, **kwargs) -> Type[ASRInterface]:
        if system_name == "Faster-Whisper":
            return FasterWhisperASR()
        elif system_name == "AzureSTT":
            return AzureASR(
                subscription_key=kwargs.get("subscription_key"),
                region=kwargs.get("region"),
                callback=kwargs.get("callback"),
            )
        else:
            raise ValueError(f"Unknown ASR system: {system_name}")
