# config_manager/character.py
from pydantic import Field, field_validator
from typing import Dict, ClassVar
from .i18n import I18nMixin, Description, MultiLingualString
from .llm import LLMConfig  # Import LLMConfig (we'll define this in llm.py later)
from .asr import ASRConfig
from .tts import TTSConfig
from .translate import TranslatorConfig

class CharacterConfig(I18nMixin):
    """
    Character configuration settings.
    """

    conf_name: str = Field(..., alias="CONF_NAME")
    conf_uid: str = Field(..., alias="CONF_UID")
    live2d_model: str = Field(..., alias="LIVE2D_MODEL")
    persona_choice: str = Field(..., alias="PERSONA_CHOICE")
    default_persona_prompt_in_yaml: str = Field(..., alias="DEFAULT_PERSONA_PROMPT_IN_YAML")
    llm_config: LLMConfig = Field(..., alias="LLM_CONFIG")
    asr_config: ASRConfig = Field(..., alias="ASR_CONFIG")
    tts_config: TTSConfig = Field(..., alias="TTS_CONFIG")
    translator: TranslatorConfig = Field(..., alias="TRANSLATOR")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "conf_name": Description.from_str("Name of the character configuration"),
        "conf_uid": Description.from_str("Unique identifier for the character configuration"),
        "live2d_model": Description.from_str("Name of the Live2D model to use"),
        "persona_choice": Description.from_str(
            "Name of the persona to use (from 'prompts/persona' directory)"
        ),
        "default_persona_prompt_in_yaml": Description.from_str(
            "Default persona prompt (used if PERSONA_CHOICE is empty)"
        ),
        "llm_config": Description.from_str("Configuration for the Language Learning Model"),
        "asr_config": Description.from_str("Configuration for Automatic Speech Recognition"),
        "tts_config": Description.from_str("Configuration for Text-to-Speech"),
        "translator": Description.from_str("Configuration for the translator"),
    }

    @field_validator("default_persona_prompt_in_yaml")
    def check_default_persona_prompt(cls, v):
        if not v:
            raise ValueError(
                "DEFAULT_PERSONA_PROMPT_IN_YAML cannot be empty if PERSONA_CHOICE is not set."
            )
        return v