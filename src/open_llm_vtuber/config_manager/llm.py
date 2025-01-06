# config_manager/llm.py
from pydantic import BaseModel, Field
from typing import Dict, ClassVar, Optional, Literal
from .i18n import I18nMixin, Description, MultiLingualString

class OpenAICompatibleConfig(I18nMixin):
    """Configuration for OpenAI-compatible LLM providers."""
    
    base_url: str = Field(..., alias="base_url")
    llm_api_key: str = Field(..., alias="llm_api_key")
    organization_id: str = Field(..., alias="organization_id")
    project_id: str = Field(..., alias="project_id")
    model: str = Field(..., alias="model")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "base_url": Description(
            en="Base URL for OpenAI-compatible API",
            zh="OpenAI兼容API的基础URL"
        ),
        "llm_api_key": Description(
            en="API key for authentication",
            zh="API 认证密钥"
        ),
        "organization_id": Description(
            en="Organization ID for the API",
            zh="组织 ID"
        ),
        "project_id": Description(
            en="Project ID for the API",
            zh="项目 ID"
        ),
        "model": Description(
            en="Name of the LLM model to use",
            zh="要使用的语言模型名称"
        ),
    }

class ClaudeConfig(I18nMixin):
    """Configuration for Claude API."""
    
    base_url: str = Field(..., alias="base_url")
    llm_api_key: str = Field(..., alias="llm_api_key")
    model: str = Field(..., alias="model")
    verbose: bool = Field(False, alias="verbose")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "base_url": Description(
            en="Base URL for Claude API",
            zh="Claude API 的基础 URL"
        ),
        "llm_api_key": Description(
            en="API key for authentication",
            zh="API 认证密钥"
        ),
        "model": Description(
            en="Name of the Claude model to use",
            zh="要使用的 Claude 模型名称"
        ),
    }

class LlamaCppConfig(I18nMixin):
    """Configuration for LlamaCpp."""
    
    model_path: str = Field(..., alias="model_path")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_path": Description(
            en="Path to the GGUF model file",
            zh="GGUF 模型文件路径"
        ),
    }
