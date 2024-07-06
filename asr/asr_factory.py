from typing import Type
from .asr_interface import ASRInterface


class ASRFactory:
    @staticmethod
    def get_asr_system(system_name: str, **kwargs) -> Type[ASRInterface]:
        if system_name == "Faster-Whisper":
            from .faster_whisper_asr import VoiceRecognition as FasterWhisperASR
            return FasterWhisperASR(
                model_path=kwargs.get("model_path"),
                download_root=kwargs.get("download_root"),
                language=kwargs.get("language"),
                device=kwargs.get("device"),
            )
        elif system_name == "WhisperCPP":
            from .whisper_cpp_asr import VoiceRecognition as WhisperCPPASR
            return WhisperCPPASR(**kwargs)
        elif system_name == "Whisper":
            from .openai_whisper_asr import VoiceRecognition as WhisperASR
            return WhisperASR(**kwargs)
        elif system_name == "AzureSTT":
            from .azure_asr import VoiceRecognition as AzureASR
            return AzureASR(
                subscription_key=kwargs.get("subscription_key"),
                region=kwargs.get("region"),
                callback=kwargs.get("callback"),
            )
        else:
            raise ValueError(f"Unknown ASR system: {system_name}")
