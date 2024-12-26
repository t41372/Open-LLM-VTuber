# config_manager/translate.py
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Literal, Optional, Dict, ClassVar, Union, Any
from .i18n import I18nMixin, Description, MultiLingualString

# --- Sub-models for specific Translator providers ---


class DeepLXConfig(I18nMixin):
    deeplx_target_lang: str = Field(..., alias="DEEPLX_TARGET_LANG")
    deeplx_api_endpoint: str = Field(..., alias="DEEPLX_API_ENDPOINT")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "deeplx_target_lang": Description.from_str(
            "Target language for DeepLX translation"
        ),
        "deeplx_api_endpoint": Description.from_str("API endpoint for DeepLX"),
    }


# --- Main TranslatorConfig model ---


class TranslatorConfig(I18nMixin):
    """
    Configuration for translation.
    """

    translate_audio: bool = Field(..., alias="TRANSLATE_AUDIO")
    translate_provider: Literal["DeepLX"] = Field(..., alias="TRANSLATE_PROVIDER")
    deeplx: Optional[DeepLXConfig] = Field(None, alias="DeepLX")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "translate_audio": Description.from_str(
            "Enable audio translation (requires DeepLX deployment)"
        ),
        "translate_provider": Description.from_str("Translation provider to use"),
        "deeplx": Description.from_str("Configuration for DeepLX translation"),
    }

    @model_validator(mode="after")
    def check_translator_config(cls, values: "TranslatorConfig", info: ValidationInfo):
        translate_audio = values.translate_audio
        translate_provider = values.translate_provider

        if translate_audio:
            if translate_provider == "DeepLX" and values.deeplx is None:
                raise ValueError(
                    "DeepLX configuration must be provided when translate_audio is True and translate_provider is 'DeepLX'"
                )

        return values
