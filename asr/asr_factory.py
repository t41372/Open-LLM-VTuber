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
        elif system_name == "FunASR":
            from .fun_asr import VoiceRecognition as FunASR
            return FunASR(
                model_name=kwargs.get("model_name"),
                vad_model=kwargs.get("vad_model"),
                punc_model=kwargs.get("punc_model"),
                ncpu=kwargs.get("ncpu"),
                hub=kwargs.get("hub"),
                device=kwargs.get("device"),
                language=kwargs.get("language"),
                use_itn=kwargs.get("use_itn"),
                # sample_rate=kwargs.get("sample_rate"),
            )
        elif system_name == "AzureASR":
            from .azure_asr import VoiceRecognition as AzureASR
            return AzureASR(
                subscription_key=kwargs.get("subscription_key"),
                region=kwargs.get("region"),
                callback=kwargs.get("callback"),
            )
        else:
            raise ValueError(f"Unknown ASR system: {system_name}")
