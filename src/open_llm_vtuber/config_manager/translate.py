# config_manager/translate.py
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Literal, Optional, Dict, ClassVar
from .i18n import I18nMixin, Description, MultiLingualString

# --- Sub-models for specific Translator providers ---


class DeepLXConfig(I18nMixin):
    """Configuration for DeepLX translation service."""
    
    deeplx_target_lang: str = Field(..., alias="deeplx_target_lang")
    deeplx_api_endpoint: str = Field(..., alias="deeplx_api_endpoint")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "deeplx_target_lang": Description(
            en="Target language code for DeepLX translation",
            zh="DeepLX 翻译的目标语言代码"
        ),
        "deeplx_api_endpoint": Description(
            en="API endpoint URL for DeepLX service",
            zh="DeepLX 服务的 API 端点 URL"
        ),
    }


# --- Main TranslatorConfig model ---


class TranslatorConfig(I18nMixin):
    """Configuration for translation services."""
    
    translate_audio: bool = Field(..., alias="translate_audio")
    translate_provider: Literal["DeepLX"] = Field(..., alias="translate_provider")
    deeplx: Optional[DeepLXConfig] = Field(None, alias="deeplx")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "translate_audio": Description(
            en="Enable audio translation (requires DeepLX deployment)",
            zh="启用音频翻译（需要部署 DeepLX）"
        ),
        "translate_provider": Description(
            en="Translation service provider to use",
            zh="要使用的翻译服务提供者"
        ),
        "deeplx": Description(
            en="Configuration for DeepLX translation service",
            zh="DeepLX 翻译服务配置"
        ),
    }

    @model_validator(mode='after')
    def check_translator_config(cls, values: "TranslatorConfig", info: ValidationInfo):
        translate_audio = values.translate_audio
        translate_provider = values.translate_provider

        if translate_audio:
            if translate_provider == "DeepLX" and values.deeplx is None:
                raise ValueError(
                    "DeepLX configuration must be provided when translate_audio is True and translate_provider is 'DeepLX'"
                )

        return values
