# config_manager/system.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, ClassVar
from .i18n import I18nMixin, Description, MultiLingualString

class SystemConfig(I18nMixin):
    """System configuration settings."""
    
    conf_version: str = Field(..., alias="conf_version")
    host: str = Field(..., alias="host") 
    port: int = Field(..., alias="port")
    preload_models: bool = Field(..., alias="preload_models")
    config_alts_dir: str = Field(..., alias="config_alts_dir")
    live2d_expression_prompt: str = Field(..., alias="live2d_expression_prompt")
    remove_special_char: bool = Field(..., alias="remove_special_char")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "conf_version": Description(
            en="Configuration version",
            zh="配置文件版本"
        ),
        "host": Description(
            en="Server host address",
            zh="服务器主机地址"
        ),
        "port": Description(
            en="Server port number",
            zh="服务器端口号"
        ),
        "preload_models": Description(
            en="Whether to preload ASR and TTS models on startup",
            zh="是否在服务器启动时预加载 ASR 和 TTS 模型"
        ),
        "config_alts_dir": Description(
            en="Directory for alternative configurations",
            zh="备用配置目录"
        ),
        "live2d_expression_prompt": Description(
            en="Prompt for Live2D expressions",
            zh="Live2D 表情提示词"
        ),
        "remove_special_char": Description(
            en="Whether to remove special characters from audio generation",
            zh="是否从音频生成中移除特殊字符"
        ),
    }
    
    @model_validator(mode='after')
    def check_port(cls, values):
        port = values.port
        if port < 0 or port > 65535:
            raise ValueError('Port must be between 0 and 65535')
        return values