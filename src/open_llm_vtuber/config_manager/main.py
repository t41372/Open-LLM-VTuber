# config_manager/main.py
from pydantic import BaseModel, Field
from typing import Dict, ClassVar

from .system import SystemConfig
from .character import CharacterConfig
from .i18n import I18nMixin, Description


class Config(I18nMixin):
    """
    Main configuration for the application.
    """

    system_config: SystemConfig = Field(..., alias="SYSTEM_CONFIG")
    character_config: CharacterConfig = Field(..., alias="CHARACTER_CONFIG")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "system_config": Description.from_str("System configuration settings"),
        "character_config": Description.from_str("Character configuration settings"),
    }
