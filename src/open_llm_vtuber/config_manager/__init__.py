"""
Configuration management package for Open LLM VTuber.

This package provides configuration management functionality through Pydantic models
and utility functions for loading/saving configurations.
"""

# Import main configuration classes
from .main import Config
from .system import SystemConfig
from .character import CharacterConfig
from .llm import (
    LLMConfig,
    OllamaConfig,
    ClaudeConfig,
    LlamaCppConfig,
    Mem0Config,
    MemGPTConfig,
    Mem0VectorStoreConfig,
    Mem0EmbedderConfig,
)
from .asr import (
    ASRConfig,
    AzureASRConfig,
    FasterWhisperConfig,
    WhisperCPPConfig,
    WhisperConfig,
    FunASRConfig,
    SherpaOnnxASRConfig,
    GroqWhisperASRConfig,
)
from .tts import (
    TTSConfig,
    AzureTTSConfig,
    BarkTTSConfig,
    EdgeTTSConfig,
    CosyvoiceTTSConfig,
    MeloTTSConfig,
    PiperTTSConfig,
    CoquiTTSConfig,
    XTTSConfig,
    GPTSoVITSConfig,
    FishAPITTSConfig,
    SherpaOnnxTTSConfig,
)
from .translate import TranslatorConfig, DeepLXConfig
from .i18n import I18nMixin, Description, MultiLingualString

# Import utility functions
from .utils import (
    read_yaml,
    validate_config,
    save_config,
    scan_config_alts_directory,
    scan_bg_directory,
)

__all__ = [
    # Main configuration classes
    "Config",
    "SystemConfig",
    "CharacterConfig",
    # LLM related classes
    "LLMConfig",
    "OllamaConfig",
    "ClaudeConfig",
    "LlamaCppConfig",
    "Mem0Config",
    "MemGPTConfig",
    "Mem0VectorStoreConfig",
    "Mem0EmbedderConfig",
    # ASR related classes
    "ASRConfig",
    "AzureASRConfig",
    "FasterWhisperConfig",
    "WhisperCPPConfig",
    "WhisperConfig",
    "FunASRConfig",
    "SherpaOnnxASRConfig",
    "GroqWhisperASRConfig",
    # TTS related classes
    "TTSConfig",
    "AzureTTSConfig",
    "BarkTTSConfig",
    "EdgeTTSConfig",
    "CosyvoiceTTSConfig",
    "MeloTTSConfig",
    "PiperTTSConfig",
    "CoquiTTSConfig",
    "XTTSConfig",
    "GPTSoVITSConfig",
    "FishAPITTSConfig",
    "SherpaOnnxTTSConfig",
    # Translation related classes
    "TranslatorConfig",
    "DeepLXConfig",
    # i18n related classes
    "I18nMixin",
    "Description",
    "MultiLingualString",
    # Utility functions
    "read_yaml",
    "validate_config",
    "save_config",
    "scan_config_alts_directory",
    "scan_bg_directory",
]
