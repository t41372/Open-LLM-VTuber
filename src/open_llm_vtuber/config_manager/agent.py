"""
This module contains the pydantic model for the configurations of
different types of agents.
"""

from pydantic import BaseModel, Field
from typing import Dict, ClassVar, Optional, Literal
from .i18n import I18nMixin, Description
from .llm import (
    OpenAICompatibleConfig,
    ClaudeConfig,
    LlamaCppConfig,
)

# ======== Configurations for different Agents ========


class BasicMemoryAgentConfig(I18nMixin, BaseModel):
    """Configuration for the basic memory agent."""

    llm_provider: Literal["openai_compatible_llm", "claude_llm", "llama_cpp_llm"] = (
        Field(..., alias="llm_provider")
    )

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "llm_provider": Description(
            en="LLM provider to use for this agent", zh="此代理使用的语言模型提供者"
        ),
    }


class Mem0VectorStoreConfig(I18nMixin, BaseModel):
    """Configuration for Mem0 vector store."""

    provider: str = Field(..., alias="provider")
    config: Dict = Field(..., alias="config")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "provider": Description(
            en="Vector store provider (e.g., qdrant)", zh="向量存储提供者（如 qdrant）"
        ),
        "config": Description(
            en="Provider-specific configuration", zh="提供者特定配置"
        ),
    }


class Mem0LLMConfig(I18nMixin, BaseModel):
    """Configuration for Mem0 LLM."""

    provider: str = Field(..., alias="provider")
    config: Dict = Field(..., alias="config")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "provider": Description(en="LLM provider name", zh="语言模型提供者名称"),
        "config": Description(
            en="Provider-specific configuration", zh="提供者特定配置"
        ),
    }


class Mem0EmbedderConfig(I18nMixin, BaseModel):
    """Configuration for Mem0 embedder."""

    provider: str = Field(..., alias="provider")
    config: Dict = Field(..., alias="config")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "provider": Description(en="Embedder provider name", zh="嵌入模型提供者名称"),
        "config": Description(
            en="Provider-specific configuration", zh="提供者特定配置"
        ),
    }


class Mem0Config(I18nMixin, BaseModel):
    """Configuration for Mem0."""

    vector_store: Mem0VectorStoreConfig = Field(..., alias="vector_store")
    llm: Mem0LLMConfig = Field(..., alias="llm")
    embedder: Mem0EmbedderConfig = Field(..., alias="embedder")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "vector_store": Description(en="Vector store configuration", zh="向量存储配置"),
        "llm": Description(en="LLM configuration", zh="语言模型配置"),
        "embedder": Description(en="Embedder configuration", zh="嵌入模型配置"),
    }


# =================================


class AgentSettings(I18nMixin, BaseModel):
    """Settings for different types of agents."""

    basic_memory_agent: Optional[BasicMemoryAgentConfig] = Field(
        None, alias="basic_memory_agent"
    )
    mem0_agent: Optional[Mem0Config] = Field(None, alias="mem0_agent")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "basic_memory_agent": Description(
            en="Configuration for basic memory agent", zh="基础记忆代理配置"
        ),
        "mem0_agent": Description(en="Configuration for Mem0 agent", zh="Mem0代理配置"),
    }


class LLMConfigs(I18nMixin, BaseModel):
    """Pool of LLM provider configurations.
    This class contains configurations for different LLM providers."""

    openai_compatible_llm: Optional[OpenAICompatibleConfig] = Field(
        None, alias="openai_compatible_llm"
    )
    claude_llm: Optional[ClaudeConfig] = Field(None, alias="claude_llm")
    llama_cpp_llm: Optional[LlamaCppConfig] = Field(None, alias="llama_cpp_llm")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "openai_compatible_llm": Description(
            en="Configuration for OpenAI-compatible LLM providers",
            zh="OpenAI兼容的语言模型提供者配置",
        ),
        "claude_llm": Description(
            en="Configuration for Claude API", zh="Claude API配置"
        ),
        "llama_cpp_llm": Description(
            en="Configuration for local Llama.cpp", zh="本地Llama.cpp配置"
        ),
    }


class AgentConfig(I18nMixin, BaseModel):
    """This class contains all of the configurations related to agent."""

    conversation_agent_choice: Literal["basic_memory_agent", "mem0_agent"] = (
        Field(..., alias="conversation_agent_choice")
    )
    agent_settings: AgentSettings = Field(..., alias="agent_settings")
    llm_configs: LLMConfigs = Field(..., alias="llm_configs")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "conversation_agent_choice": Description(
            en="Type of conversation agent to use", zh="要使用的对话代理类型"
        ),
        "agent_settings": Description(
            en="Settings for different agent types", zh="不同代理类型的设置"
        ),
        "llm_configs": Description(
            en="Pool of LLM provider configurations", zh="语言模型提供者配置池"
        ),
    }
