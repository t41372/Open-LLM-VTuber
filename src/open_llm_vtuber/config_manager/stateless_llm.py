# config_manager/llm.py
from pydantic import BaseModel, Field
from typing import Dict, ClassVar, Optional
from .i18n import I18nMixin, Description


class OpenAICompatibleConfig(I18nMixin):
    """Configuration for OpenAI-compatible LLM providers."""

    base_url: str = Field(..., alias="base_url")
    llm_api_key: str = Field(..., alias="llm_api_key")
    model: str = Field(..., alias="model")
    organization_id: str | None = Field(None, alias="organization_id")
    project_id: str | None = Field(None, alias="project_id")
    temperature: float = Field(1.0, alias="temperature")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "base_url": Description(en="Base URL for the API endpoint", zh="API的URL端点"),
        "llm_api_key": Description(en="API key for authentication", zh="API 认证密钥"),
        "organization_id": Description(
            en="Organization ID for the API (Optional)", zh="组织 ID (可选)"
        ),
        "project_id": Description(
            en="Project ID for the API (Optional)", zh="项目 ID (可选)"
        ),
        "model": Description(en="Name of the LLM model to use", zh="LLM 模型名称"),
        "temperature": Description(
            en="What sampling temperature to use, between 0 and 2.",
            zh="使用的采样温度，介于 0 和 2 之间。",
        ),
    }


# Ollama config is completely the same as OpenAICompatibleConfig


class OllamaConfig(OpenAICompatibleConfig):
    """Configuration for Ollama API."""

    llm_api_key: str = Field("default_api_key", alias="llm_api_key")
    keep_alive: float = Field(-1, alias="keep_alive")
    unload_at_exit: bool = Field(True, alias="unload_at_exit")


class OpenAIConfig(OpenAICompatibleConfig):
    """Configuration for Official OpenAI API."""

    base_url: str = Field("https://api.openai.com/v1", alias="base_url")


class GeminiConfig(OpenAICompatibleConfig):
    """Configuration for Gemini API."""

    base_url: str = Field(
        "https://generativelanguage.googleapis.com/v1beta/openai/", alias="base_url"
    )


class ZhipuConfig(OpenAICompatibleConfig):
    """Configuration for Zhipu API."""

    base_url: str = Field("https://open.bigmodel.cn/api/paas/v4/", alias="base_url")


class DeepseekConfig(OpenAICompatibleConfig):
    """Configuration for Deepseek API."""

    base_url: str = Field("https://api.deepseek.com/v1", alias="base_url")


class GroqConfig(OpenAICompatibleConfig):
    """Configuration for Groq API."""

    base_url: str = Field("https://api.groq.com/openai/v1", alias="base_url")


class ClaudeConfig(I18nMixin):
    """Configuration for OpenAI Official API."""

    base_url: str = Field("https://api.anthropic.com", alias="base_url")
    llm_api_key: str = Field(..., alias="llm_api_key")
    model: str = Field(..., alias="model")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "base_url": Description(
            en="Base URL for Claude API", zh="Claude API 的API端点"
        ),
        "llm_api_key": Description(en="API key for authentication", zh="API 认证密钥"),
        "model": Description(
            en="Name of the Claude model to use", zh="要使用的 Claude 模型名称"
        ),
    }


class LlamaCppConfig(I18nMixin):
    """Configuration for LlamaCpp."""

    model_path: str = Field(..., alias="model_path")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_path": Description(
            en="Path to the GGUF model file", zh="GGUF 模型文件路径"
        ),
    }


class StatelessLLMConfigs(I18nMixin, BaseModel):
    """Pool of LLM provider configurations.
    This class contains configurations for different LLM providers."""

    openai_compatible_llm: Optional[OpenAICompatibleConfig] = Field(
        None, alias="openai_compatible_llm"
    )
    ollama_llm: Optional[OllamaConfig] = Field(None, alias="ollama_llm")
    openai_llm: Optional[OpenAIConfig] = Field(None, alias="openai_llm")
    gemini_llm: Optional[GeminiConfig] = Field(None, alias="gemini_llm")
    zhipu_llm: Optional[ZhipuConfig] = Field(None, alias="zhipu_llm")
    deepseek_llm: Optional[DeepseekConfig] = Field(None, alias="deepseek_llm")
    groq_llm: Optional[GroqConfig] = Field(None, alias="groq_llm")
    claude_llm: Optional[ClaudeConfig] = Field(None, alias="claude_llm")
    llama_cpp_llm: Optional[LlamaCppConfig] = Field(None, alias="llama_cpp_llm")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "openai_compatible_llm": Description(
            en="Configuration for OpenAI-compatible LLM providers",
            zh="OpenAI兼容的语言模型提供者配置",
        ),
        "ollama_llm": Description(en="Configuration for Ollama", zh="Ollama 配置"),
        "openai_llm": Description(
            en="Configuration for Official OpenAI API", zh="官方 OpenAI API 配置"
        ),
        "gemini_llm": Description(
            en="Configuration for Gemini API", zh="Gemini API 配置"
        ),
        "zhipu_llm": Description(en="Configuration for Zhipu API", zh="Zhipu API 配置"),
        "deepseek_llm": Description(
            en="Configuration for Deepseek API", zh="Deepseek API 配置"
        ),
        "groq_llm": Description(en="Configuration for Groq API", zh="Groq API 配置"),
        "claude_llm": Description(
            en="Configuration for Claude API", zh="Claude API配置"
        ),
        "llama_cpp_llm": Description(
            en="Configuration for local Llama.cpp", zh="本地Llama.cpp配置"
        ),
    }
