# config_manager/system.py
from pydantic import Field, field_validator, model_validator
from typing import Literal, Dict, ClassVar
from .i18n import I18nMixin, Description, MultiLingualString  # Import from i18n.py

class SystemConfig(I18nMixin):
    """
    System configuration settings.
    """

    conf_version: str = Field(..., alias="CONF_VERSION")
    protocal: str = Field(..., alias="PROTOCAL")
    host: str = Field(..., alias="HOST")
    port: int = Field(..., alias="PORT")
    preload_models: bool = Field(..., alias="PRELOAD_MODELS")
    config_alts_dir: str = Field(..., alias="CONFIG_ALTS_DIR")
    live2d_expression_prompt: str = Field(..., alias="LIVE2D_Expression_Prompt")
    remove_special_char: bool = Field(..., alias="REMOVE_SPECIAL_CHAR")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "conf_version": Description.from_str("Version of the configuration file"),
        "protocal": Description.from_str("Protocol to use for the server (e.g., http://)"),
        "host": Description.from_str("Host address of the server (e.g., localhost)"),
        "port": Description.from_str("Port number for the server"),
        "preload_models": Description.from_str("If True, ASR and TTS models will be initialized when the server starts and kept in memory"),
        "config_alts_dir": Description.from_str("Directory for alternative configurations"),
        "live2d_expression_prompt": Description.from_str(
            "Prompt appended to the end of the system prompt to control Live2D facial expressions"
        ),
        "remove_special_char": Description.from_str("If True, special characters like emojis will be removed from audio generation"),
    }

    @field_validator('protocal')
    def check_protocal(cls, v):
        if not v.endswith("://"):
            raise ValueError('protocal should end with ://')
        return v
    
    @model_validator(mode='after')
    def check_port(cls, values):
        port = values.port
        if port < 0 or port > 65535:
            raise ValueError('port should be between 0 and 65535')
        return values