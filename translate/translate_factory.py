from .deeplx import DeepLXTranslate
from .translate_interface import TranslateInterface

class TranslateFactory:
    @staticmethod
    def get_translator(translate_provider:str, **kwargs) -> TranslateInterface:
        translate_provider = translate_provider.lower()
        if translate_provider == "deeplx":
            return DeepLXTranslate(
                api_endpoint=kwargs.get("DEEPLX_API_ENDPOINT"),
                target_lang=kwargs.get("DEEPLX_TARGET_LANG")
            )
        else:
            raise ValueError(f"Unsupported translate provider: {translate_provider}")