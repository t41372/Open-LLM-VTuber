# config_manager/llm.py
from pydantic import BaseModel, Field
from typing import Dict, ClassVar, Optional, Literal
from .i18n import I18nMixin, Description, MultiLingualString

class OllamaConfig(I18nMixin):
    """Configuration for Ollama LLM provider."""
    
    base_url: str = Field(..., alias="base_url")
    llm_api_key: str = Field(..., alias="llm_api_key")
    organization_id: str = Field(..., alias="organization_id")
    project_id: str = Field(..., alias="project_id")
    model: str = Field(..., alias="model")
    verbose: bool = Field(False, alias="verbose")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "base_url": Description(
            en="Base URL for Ollama API",
            zh="Ollama API 的基础 URL"
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
        "verbose": Description(
            en="Enable verbose output",
            zh="启用详细输出"
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
        "verbose": Description(
            en="Enable verbose output",
            zh="启用详细输出"
        ),
    }

class LlamaCppConfig(I18nMixin):
    """Configuration for LlamaCpp."""
    
    model_path: str = Field(..., alias="model_path")
    verbose: bool = Field(True, alias="verbose")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_path": Description(
            en="Path to the GGUF model file",
            zh="GGUF 模型文件路径"
        ),
        "verbose": Description(
            en="Enable verbose output",
            zh="启用详细输出"
        ),
    }

class Mem0VectorStoreConfig(I18nMixin):
    """Configuration for Mem0 vector store."""
    
    provider: str = Field(..., alias="provider")
    config: Dict = Field(..., alias="config")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "provider": Description(
            en="Vector store provider (e.g., qdrant)",
            zh="向量存储提供者（如 qdrant）"
        ),
        "config": Description(
            en="Provider-specific configuration",
            zh="提供者特定配置"
        ),
    }

class Mem0LLMConfig(I18nMixin):
    """Configuration for Mem0 LLM."""
    
    provider: str = Field(..., alias="provider")
    config: Dict = Field(..., alias="config")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "provider": Description(
            en="LLM provider name",
            zh="语言模型提供者名称"
        ),
        "config": Description(
            en="Provider-specific configuration",
            zh="提供者特定配置"
        ),
    }

class Mem0EmbedderConfig(I18nMixin):
    """Configuration for Mem0 embedder."""
    
    provider: str = Field(..., alias="provider")
    config: Dict = Field(..., alias="config")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "provider": Description(
            en="Embedder provider name",
            zh="嵌入模型提供者名称"
        ),
        "config": Description(
            en="Provider-specific configuration",
            zh="提供者特定配置"
        ),
    }

class Mem0Config(I18nMixin):
    """Configuration for Mem0."""
    
    vector_store: Mem0VectorStoreConfig = Field(..., alias="vector_store")
    llm: Mem0LLMConfig = Field(..., alias="llm")
    embedder: Mem0EmbedderConfig = Field(..., alias="embedder")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "vector_store": Description(
            en="Vector store configuration",
            zh="向量存储配置"
        ),
        "llm": Description(
            en="LLM configuration",
            zh="语言模型配置"
        ),
        "embedder": Description(
            en="Embedder configuration",
            zh="嵌入模型配置"
        ),
    }

class MemGPTConfig(I18nMixin):
    """Configuration for MemGPT."""
    
    base_url: str = Field(..., alias="base_url")
    admin_token: str = Field(..., alias="admin_token")
    agent_id: str = Field(..., alias="agent_id")
    verbose: bool = Field(True, alias="verbose")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "base_url": Description(
            en="Base URL for MemGPT server",
            zh="MemGPT 服务器基础 URL"
        ),
        "admin_token": Description(
            en="Admin token for authentication",
            zh="管理员认证令牌"
        ),
        "agent_id": Description(
            en="ID of the agent to use",
            zh="要使用的代理 ID"
        ),
        "verbose": Description(
            en="Enable verbose output",
            zh="启用详细输出"
        ),
    }

class LLMConfig(I18nMixin):
    """Configuration for Language Learning Models."""
    
    llm_provider: Literal["ollama_llm", "memgpt", "mem0", "claude_llm", "llama_cpp_llm", "fake_llm"] = Field(..., alias="llm_provider")
    ollama_llm: Optional[OllamaConfig] = Field(None, alias="ollama")
    claude_llm: Optional[ClaudeConfig] = Field(None, alias="claude")
    llama_cpp_llm: Optional[LlamaCppConfig] = Field(None, alias="llamacpp")
    mem0: Optional[Mem0Config] = Field(None, alias="mem0")
    memgpt: Optional[MemGPTConfig] = Field(None, alias="memgpt")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "llm_provider": Description(
            en="LLM Provider",
            zh="语言模型提供者"
        ),
        "ollama_llm": Description(
            en="Configuration for Ollama (and any OpenAI-Compatible backend)",
            zh="Ollama (以及所有支持 OpenAI 格式的后端) 的配置"
        ),
        "claude_llm": Description(
            en="Configuration for Claude API",
            zh="Claude API 配置"
        ),
        "llama_cpp_llm": Description(
            en="Configuration for Llama CPP that runs directly in the backend",
            zh="LlamaCpp 配置 (直接在后端运行)"
        ),
        "mem0": Description(
            en="Configuration for Mem0",
            zh="Mem0 配置"
        ),
        "memgpt": Description(
            en="Configuration for MemGPT",
            zh="MemGPT 配置"
        ),
    }
