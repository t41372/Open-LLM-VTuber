from .tts_interface import TTSInterface
from .azureTTS import TTSEngine as AzureTTSEngine
from .barkTTS import TTSEngine as BarkTTSEngine
from .edgeTTS import TTSEngine as EdgeTTSEngine
from .pyttsx3TTS import TTSEngine as Pyttsx3TTSEngine
from typing import Type


class TTSFactory:
    @staticmethod
    def get_tts_engine(engine_type, **kwargs) -> Type[TTSInterface]:
        if engine_type == "AzureTTS":
            return AzureTTSEngine(kwargs.get("api_key"), kwargs.get("region"), kwargs.get("voice"))
        elif engine_type == "barkTTS":
            return BarkTTSEngine()
        elif engine_type == "edgeTTS":
            return EdgeTTSEngine()
        elif engine_type == "pyttsx3TTS":
            return Pyttsx3TTSEngine()
        else:
            raise ValueError(f"Unknown TTS engine type: {engine_type}")

# Example usage:
# tts_engine = TTSFactory.get_tts_engine("azure", api_key="your_api_key", region="your_region", voice="your_voice")
# tts_engine.speak("Hello world")