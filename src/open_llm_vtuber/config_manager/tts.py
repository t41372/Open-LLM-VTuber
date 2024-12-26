# config_manager/tts.py
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Literal, Optional, Dict, ClassVar, Union, Any
from .i18n import I18nMixin, Description, MultiLingualString

# --- Sub-models for specific TTS providers ---


class AzureTTSConfig(I18nMixin):
    api_key: str = Field(..., alias="api_key")
    region: str = Field(..., alias="region")
    voice: str = Field(..., alias="voice")
    pitch: str = Field(..., alias="pitch")
    rate: str = Field(..., alias="rate")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_key": Description.from_str("API key for Azure TTS"),
        "region": Description.from_str("Region for Azure TTS (e.g., eastus)"),
        "voice": Description.from_str("Voice name to use for Azure TTS"),
        "pitch": Description.from_str("Pitch adjustment for Azure TTS (percentage)"),
        "rate": Description.from_str("Speaking rate for Azure TTS"),
    }


class BarkTTSConfig(I18nMixin):
    voice: str = Field(..., alias="voice")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "voice": Description.from_str("Voice name to use for Bark TTS"),
    }


class EdgeTTSConfig(I18nMixin):
    voice: str = Field(..., alias="voice")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "voice": Description.from_str(
            "Voice name to use for Edge TTS",
            "Use `edge-tts --list-voices` to list available voices",
        ),
    }


class CosyvoiceTTSConfig(I18nMixin):
    client_url: str = Field(..., alias="client_url")
    mode_checkbox_group: str = Field(..., alias="mode_checkbox_group")
    sft_dropdown: str = Field(..., alias="sft_dropdown")
    prompt_text: str = Field(..., alias="prompt_text")
    prompt_wav_upload_url: str = Field(..., alias="prompt_wav_upload_url")
    prompt_wav_record_url: str = Field(..., alias="prompt_wav_record_url")
    instruct_text: str = Field(..., alias="instruct_text")
    seed: int = Field(..., alias="seed")
    api_name: str = Field(..., alias="api_name")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "client_url": Description.from_str("URL of the CosyVoice Gradio web UI"),
        "mode_checkbox_group": Description.from_str("Mode checkbox group value"),
        "sft_dropdown": Description.from_str("SFT dropdown value"),
        "prompt_text": Description.from_str("Prompt text"),
        "prompt_wav_upload_url": Description.from_str(
            "URL for uploading prompt WAV file"
        ),
        "prompt_wav_record_url": Description.from_str("URL for recording prompt WAV"),
        "instruct_text": Description.from_str("Instruction text"),
        "seed": Description.from_str("Seed value"),
        "api_name": Description.from_str("API endpoint name"),
    }


class MeloTTSConfig(I18nMixin):
    speaker: str = Field(..., alias="speaker")
    language: str = Field(..., alias="language")
    device: str = Field(..., alias="device")
    speed: float = Field(..., alias="speed")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "speaker": Description.from_str("Speaker name for Melo TTS"),
        "language": Description.from_str("Language code for Melo TTS"),
        "device": Description.from_str("Device to use for inference (e.g., cpu, cuda)"),
        "speed": Description.from_str("Speed of speech"),
    }


class PiperTTSConfig(I18nMixin):
    voice_model_path: str = Field(..., alias="voice_model_path")
    verbose: bool = Field(False, alias="verbose")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "voice_model_path": Description.from_str("Path to the Piper TTS voice model"),
        "verbose": Description.from_str("Enable verbose output"),
    }


class xTTSConfig(I18nMixin):
    api_url: str = Field(..., alias="api_url")
    speaker_wav: str = Field(..., alias="speaker_wav")
    language: str = Field(..., alias="language")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_url": Description.from_str("API URL for xTTS"),
        "speaker_wav": Description.from_str("Speaker WAV file or identifier for xTTS"),
        "language": Description.from_str("Language code for xTTS"),
    }


class GPTSoVITSConfig(I18nMixin):
    api_url: str = Field(..., alias="api_url")
    text_lang: str = Field(..., alias="text_lang")
    ref_audio_path: str = Field(..., alias="ref_audio_path")
    prompt_lang: str = Field(..., alias="prompt_lang")
    prompt_text: str = Field(..., alias="prompt_text")
    text_split_method: str = Field(..., alias="text_split_method")
    batch_size: str = Field(..., alias="batch_size")
    media_type: str = Field(..., alias="media_type")
    streaming_mode: str = Field(..., alias="streaming_mode")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_url": Description.from_str("API URL for GPT-SoVITS"),
        "text_lang": Description.from_str("Language code for input text"),
        "ref_audio_path": Description.from_str("Path to reference audio file"),
        "prompt_lang": Description.from_str("Language code for prompt text"),
        "prompt_text": Description.from_str("Prompt text"),
        "text_split_method": Description.from_str("Method for splitting text"),
        "batch_size": Description.from_str("Batch size"),
        "media_type": Description.from_str("Media type (e.g., wav)"),
        "streaming_mode": Description.from_str("Streaming mode (true or false)"),
    }


class FishAPITTSConfig(I18nMixin):
    api_key: str = Field(..., alias="api_key")
    reference_id: str = Field(..., alias="reference_id")
    latency: Literal["normal", "balanced"] = Field("balanced", alias="latency")
    base_url: str = Field("https://api.fish.audio", alias="base_url")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_key": Description.from_str("API key for Fish TTS"),
        "reference_id": Description.from_str("Reference ID for the voice"),
        "latency": Description.from_str("Latency mode (normal or balanced)"),
        "base_url": Description.from_str("Base URL for the Fish TTS API"),
    }


class CoquiTTSConfig(I18nMixin):
    model_name: str = Field(..., alias="model_name")
    speaker_wav: Optional[str] = Field(None, alias="speaker_wav")
    language: Optional[str] = Field(None, alias="language")
    device: Optional[str] = Field(None, alias="device")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_name": Description.from_str(
            "Name of the Coqui TTS model to use",
            "Use `tts --list_models` to list supported models",
        ),
        "speaker_wav": Description.from_str(
            "Path to speaker WAV file for voice cloning (multi-speaker only)"
        ),
        "language": Description.from_str(
            "Language code for multi-lingual models (e.g., en, zh, ja)"
        ),
        "device": Description.from_str(
            "Device to run model on (cuda, cpu, or leave empty for auto-detect)"
        ),
    }


class SherpaOnnxTTSConfig(I18nMixin):
    vits_model: str = Field(..., alias="vits_model")
    vits_lexicon: Optional[str] = Field(None, alias="vits_lexicon")
    vits_tokens: str = Field(..., alias="vits_tokens")
    vits_data_dir: Optional[str] = Field(None, alias="vits_data_dir")
    vits_dict_dir: Optional[str] = Field(None, alias="vits_dict_dir")
    tts_rule_fsts: Optional[str] = Field(None, alias="tts_rule_fsts")
    max_num_sentences: int = Field(2, alias="max_num_sentences")
    sid: int = Field(1, alias="sid")
    provider: Literal["cpu", "cuda", "coreml"] = Field("cpu", alias="provider")
    num_threads: int = Field(1, alias="num_threads")
    speed: float = Field(1.0, alias="speed")
    debug: bool = Field(False, alias="debug")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "vits_model": Description.from_str("Path to VITS model file"),
        "vits_lexicon": Description.from_str("Path to lexicon file (optional)"),
        "vits_tokens": Description.from_str("Path to tokens file"),
        "vits_data_dir": Description.from_str("Path to espeak-ng data (optional)"),
        "vits_dict_dir": Description.from_str(
            "Path to Jieba dict (optional, for Chinese)"
        ),
        "tts_rule_fsts": Description.from_str("Path to rule FSTs file (optional)"),
        "max_num_sentences": Description.from_str(
            "Max sentences per batch (or -1 for all)"
        ),
        "sid": Description.from_str("Speaker ID (for multi-speaker models)"),
        "provider": Description.from_str("Use cpu, cuda (GPU), or coreml (Apple)"),
        "num_threads": Description.from_str("Number of computation threads"),
        "speed": Description.from_str("Speech speed (1.0 is normal)"),
        "debug": Description.from_str("Enable debug mode (True/False)"),
    }


# --- Main TTSConfig model ---


class TTSConfig(I18nMixin):
    """
    Configuration for Text-to-Speech.
    """

    tts_on: bool = Field(..., alias="TTS_ON")
    tts_model: Literal[
        "AzureTTS",
        "pyttsx3TTS",
        "edgeTTS",
        "barkTTS",
        "cosyvoiceTTS",
        "meloTTS",
        "piperTTS",
        "coquiTTS",
        "xTTS",
        "GPTSoVITS",
        "fishAPITTS",
        "SherpaOnnxTTS",
    ] = Field(..., alias="TTS_MODEL")
    azure_tts: Optional[AzureTTSConfig] = Field(None, alias="AzureTTS")
    bark_tts: Optional[BarkTTSConfig] = Field(None, alias="barkTTS")
    edge_tts: Optional[EdgeTTSConfig] = Field(None, alias="edgeTTS")
    cosyvoice_tts: Optional[CosyvoiceTTSConfig] = Field(None, alias="cosyvoiceTTS")
    melo_tts: Optional[MeloTTSConfig] = Field(None, alias="meloTTS")
    piper_tts: Optional[PiperTTSConfig] = Field(None, alias="piperTTS")
    coqui_tts: Optional[CoquiTTSConfig] = Field(None, alias="coquiTTS")
    x_tts: Optional[xTTSConfig] = Field(None, alias="xTTS")
    gpt_sovits: Optional[GPTSoVITSConfig] = Field(None, alias="GPTSoVITS")
    fish_api_tts: Optional[FishAPITTSConfig] = Field(None, alias="fishAPITTS")
    sherpa_onnx_tts: Optional[SherpaOnnxTTSConfig] = Field(None, alias="SherpaOnnxTTS")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "tts_on": Description.from_str("Enable Text-to-Speech"),
        "tts_model": Description.from_str(
            "Text-to-speech model to use",
            "Options: AzureTTS, pyttsx3TTS, edgeTTS, barkTTS, cosyvoiceTTS, meloTTS, piperTTS, coquiTTS, xTTS, GPTSoVITS, fishAPITTS, SherpaOnnxTTS",
        ),
        "azure_tts": Description.from_str("Configuration for Azure TTS"),
        "bark_tts": Description.from_str("Configuration for Bark TTS"),
        "edge_tts": Description.from_str("Configuration for Edge TTS"),
        "cosyvoice_tts": Description.from_str("Configuration for Cosyvoice TTS"),
        "melo_tts": Description.from_str("Configuration for Melo TTS"),
        "piper_tts": Description.from_str("Configuration for Piper TTS"),
        "coqui_tts": Description.from_str("Configuration for Coqui TTS"),
        "x_tts": Description.from_str("Configuration for xTTS"),
        "gpt_sovits": Description.from_str("Configuration for GPT-SoVITS"),
        "fish_api_tts": Description.from_str("Configuration for Fish API TTS"),
        "sherpa_onnx_tts": Description.from_str("Configuration for Sherpa Onnx TTS"),
    }

    @model_validator(mode="after")
    def check_tts_config(cls, values: "TTSConfig", info: ValidationInfo):
        tts_model = values.tts_model
        if tts_model == "AzureTTS" and values.azure_tts is None:
            raise ValueError(
                "AzureTTS configuration must be provided when tts_model is 'AzureTTS'"
            )
        if tts_model == "barkTTS" and values.bark_tts is None:
            raise ValueError(
                "barkTTS configuration must be provided when tts_model is 'barkTTS'"
            )
        if tts_model == "edgeTTS" and values.edge_tts is None:
            raise ValueError(
                "edgeTTS configuration must be provided when tts_model is 'edgeTTS'"
            )
        if tts_model == "cosyvoiceTTS" and values.cosyvoice_tts is None:
            raise ValueError(
                "cosyvoiceTTS configuration must be provided when tts_model is 'cosyvoiceTTS'"
            )
        if tts_model == "meloTTS" and values.melo_tts is None:
            raise ValueError(
                "meloTTS configuration must be provided when tts_model is 'meloTTS'"
            )
        if tts_model == "piperTTS" and values.piper_tts is None:
            raise ValueError(
                "piperTTS configuration must be provided when tts_model is 'piperTTS'"
            )
        if tts_model == "coquiTTS" and values.coqui_tts is None:
            raise ValueError(
                "coquiTTS configuration must be provided when tts_model is 'coquiTTS'"
            )
        if tts_model == "xTTS" and values.x_tts is None:
            raise ValueError(
                "xTTS configuration must be provided when tts_model is 'xTTS'"
            )
        if tts_model == "GPTSoVITS" and values.gpt_sovits is None:
            raise ValueError(
                "GPTSoVITS configuration must be provided when tts_model is 'GPTSoVITS'"
            )
        if tts_model == "fishAPITTS" and values.fish_api_tts is None:
            raise ValueError(
                "fishAPITTS configuration must be provided when tts_model is 'fishAPITTS'"
            )
        if tts_model == "SherpaOnnxTTS" and values.sherpa_onnx_tts is None:
            raise ValueError(
                "SherpaOnnxTTS configuration must be provided when tts_model is 'SherpaOnnxTTS'"
            )

        return values
