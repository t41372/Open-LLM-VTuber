# config_manager/asr.py
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Literal, Optional, Dict, ClassVar, Union, Any
from .i18n import I18nMixin, Description, MultiLingualString

# --- Sub-models for specific ASR providers ---


class AzureASRConfig(I18nMixin):
    api_key: str = Field(..., alias="api_key")
    region: str = Field(..., alias="region")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_key": Description.from_str("API key for Azure ASR"),
        "region": Description.from_str("Region for Azure ASR (e.g., eastus)"),
    }


class FasterWhisperConfig(I18nMixin):
    model_path: str = Field(..., alias="model_path")
    download_root: str = Field(..., alias="download_root")
    language: Optional[str] = Field(None, alias="language")
    device: Literal["auto", "cpu", "cuda"] = Field("auto", alias="device")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_path": Description.from_str(
            "Path to the Faster Whisper model",
            "distil-medium.en is an English-only model. Use distil-large-v3 for better performance if you have a good GPU.",
        ),
        "download_root": Description.from_str("Root directory for downloading models"),
        "language": Description.from_str(
            "Language code (e.g., en, zh) or None for auto-detect"
        ),
        "device": Description.from_str(
            "Device to use for inference (cpu, cuda, or auto)"
        ),
    }

    @field_validator("language")
    def check_language(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError("language must be a string or None")
        return v


class WhisperCPPConfig(I18nMixin):
    model_name: str = Field(..., alias="model_name")
    model_dir: str = Field(..., alias="model_dir")
    print_realtime: bool = Field(False, alias="print_realtime")
    print_progress: bool = Field(False, alias="print_progress")
    language: Literal["auto", "en", "zh"] = Field("auto", alias="language")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_name": Description.from_str("Name of the Whisper model"),
        "model_dir": Description.from_str("Directory for Whisper models"),
        "print_realtime": Description.from_str("Print output in real-time"),
        "print_progress": Description.from_str("Print progress information"),
        "language": Description.from_str("Language code (en, zh, or auto)"),
    }


class WhisperConfig(I18nMixin):
    name: str = Field(..., alias="name")
    download_root: str = Field(..., alias="download_root")
    device: Literal["cpu", "cuda"] = Field("cpu", alias="device")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "name": Description.from_str("Name of the Whisper model"),
        "download_root": Description.from_str("Root directory for downloading models"),
        "device": Description.from_str("Device to use for inference (cpu or cuda)"),
    }


class FunASRConfig(I18nMixin):
    model_name: str = Field("iic/SenseVoiceSmall", alias="model_name")
    vad_model: str = Field("fsmn-vad", alias="vad_model")
    punc_model: str = Field("ct-punc", alias="punc_model")
    device: Literal["cpu", "cuda"] = Field("cpu", alias="device")
    disable_update: bool = Field(True, alias="disable_update")
    ncpu: int = Field(4, alias="ncpu")
    hub: Literal["ms", "hf"] = Field("ms", alias="hub")
    use_itn: bool = Field(False, alias="use_itn")
    language: Literal["auto", "zh", "en"] = Field("auto", alias="language")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_name": Description.from_str("Name of the FunASR model"),
        "vad_model": Description.from_str("VAD model (used for audio longer than 30s)"),
        "punc_model": Description.from_str("Punctuation model"),
        "device": Description.from_str("Device to use for inference (cpu or cuda)"),
        "disable_update": Description.from_str(
            "Disable checking for FunASR updates on launch"
        ),
        "ncpu": Description.from_str("Number of threads for CPU internal operations"),
        "hub": Description.from_str(
            "Model hub to use (ms for ModelScope, hf for Hugging Face)"
        ),
        "use_itn": Description.from_str("Enable inverse text normalization"),
        "language": Description.from_str("Language code (zh, en, or auto)"),
    }


class SherpaOnnxASRConfig(I18nMixin):
    model_type: Literal[
        "transducer",
        "paraformer",
        "nemo_ctc",
        "wenet_ctc",
        "whisper",
        "tdnn_ctc",
        "sense_voice",
    ] = Field(..., alias="model_type")
    encoder: Optional[str] = Field(None, alias="encoder")
    decoder: Optional[str] = Field(None, alias="decoder")
    joiner: Optional[str] = Field(None, alias="joiner")
    paraformer: Optional[str] = Field(None, alias="paraformer")
    nemo_ctc: Optional[str] = Field(None, alias="nemo_ctc")
    wenet_ctc: Optional[str] = Field(None, alias="wenet_ctc")
    tdnn_model: Optional[str] = Field(None, alias="tdnn_model")
    whisper_encoder: Optional[str] = Field(None, alias="whisper_encoder")
    whisper_decoder: Optional[str] = Field(None, alias="whisper_decoder")
    sense_voice: Optional[str] = Field(None, alias="sense_voice")
    tokens: Optional[str] = Field(None, alias="tokens")
    hotwords_file: Optional[str] = Field(None, alias="hotwords_file")
    hotwords_score: Optional[float] = Field(None, alias="hotwords_score")
    modeling_unit: Optional[str] = Field(None, alias="modeling_unit")
    bpe_vocab: Optional[str] = Field(None, alias="bpe_vocab")
    num_threads: int = Field(4, alias="num_threads")
    whisper_language: Optional[str] = Field(None, alias="whisper_language")
    whisper_task: Literal["transcribe", "translate"] = Field(
        "transcribe", alias="whisper_task"
    )
    whisper_tail_paddings: int = Field(-1, alias="whisper_tail_paddings")
    blank_penalty: float = Field(0.0, alias="blank_penalty")
    decoding_method: Literal["greedy_search", "modified_beam_search"] = Field(
        "greedy_search", alias="decoding_method"
    )
    debug: bool = Field(False, alias="debug")
    sample_rate: int = Field(16000, alias="sample_rate")
    feature_dim: int = Field(80, alias="feature_dim")
    use_itn: bool = Field(True, alias="use_itn")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_type": Description.from_str("Type of Sherpa Onnx ASR model"),
        "encoder": Description.from_str("Path to the encoder model (for transducer)"),
        "decoder": Description.from_str("Path to the decoder model (for transducer)"),
        "joiner": Description.from_str("Path to the joiner model (for transducer)"),
        "paraformer": Description.from_str(
            "Path to the paraformer model (for paraformer)"
        ),
        "nemo_ctc": Description.from_str("Path to the NeMo CTC model (for nemo_ctc)"),
        "wenet_ctc": Description.from_str(
            "Path to the WeNet CTC model (for wenet_ctc)"
        ),
        "tdnn_model": Description.from_str("Path to the TDNN CTC model (for tdnn_ctc)"),
        "whisper_encoder": Description.from_str(
            "Path to the Whisper encoder model (for whisper)"
        ),
        "whisper_decoder": Description.from_str(
            "Path to the Whisper decoder model (for whisper)"
        ),
        "sense_voice": Description.from_str(
            "Path to the SenseVoice model (for sense_voice)"
        ),
        "tokens": Description.from_str(
            "Path to tokens.txt (required for all model types)"
        ),
        "hotwords_file": Description.from_str(
            "Path to hotwords file (if using hotwords)"
        ),
        "hotwords_score": Description.from_str("Score for hotwords"),
        "modeling_unit": Description.from_str(
            "Modeling unit for hotwords (if applicable)"
        ),
        "bpe_vocab": Description.from_str("Path to BPE vocabulary (if applicable)"),
        "num_threads": Description.from_str("Number of threads"),
        "whisper_language": Description.from_str(
            "Language for Whisper models (e.g., en, zh, etc. - if using Whisper)"
        ),
        "whisper_task": Description.from_str(
            "Task for Whisper models (transcribe or translate - if using Whisper)"
        ),
        "whisper_tail_paddings": Description.from_str(
            "Tail padding for Whisper models (if using Whisper)"
        ),
        "blank_penalty": Description.from_str("Penalty for blank symbol"),
        "decoding_method": Description.from_str(
            "Decoding method (greedy_search or modified_beam_search)"
        ),
        "debug": Description.from_str("Enable debug mode"),
        "sample_rate": Description.from_str(
            "Sample rate (should match the model's expected sample rate)"
        ),
        "feature_dim": Description.from_str(
            "Feature dimension (should match the model's expected feature dimension)"
        ),
        "use_itn": Description.from_str(
            "Enable ITN for SenseVoice models (should set to False if not using SenseVoice models)"
        ),
    }

    @model_validator(mode="after")
    def check_model_type_fields(
        cls, values: "SherpaOnnxASRConfig", info: ValidationInfo
    ):
        model_type = values.model_type
        if model_type == "transducer":
            if not all([values.encoder, values.decoder, values.joiner, values.tokens]):
                raise ValueError(
                    "encoder, decoder, joiner, and tokens must be provided for transducer model type"
                )
        elif model_type == "paraformer":
            if not all([values.paraformer, values.tokens]):
                raise ValueError(
                    "paraformer and tokens must be provided for paraformer model type"
                )
        elif model_type == "nemo_ctc":
            if not all([values.nemo_ctc, values.tokens]):
                raise ValueError(
                    "nemo_ctc and tokens must be provided for nemo_ctc model type"
                )
        elif model_type == "wenet_ctc":
            if not all([values.wenet_ctc, values.tokens]):
                raise ValueError(
                    "wenet_ctc and tokens must be provided for wenet_ctc model type"
                )
        elif model_type == "tdnn_ctc":
            if not all([values.tdnn_model, values.tokens]):
                raise ValueError(
                    "tdnn_model and tokens must be provided for tdnn_ctc model type"
                )
        elif model_type == "whisper":
            if not all([values.whisper_encoder, values.whisper_decoder, values.tokens]):
                raise ValueError(
                    "whisper_encoder, whisper_decoder, and tokens must be provided for whisper model type"
                )
        elif model_type == "sense_voice":
            if not all([values.sense_voice, values.tokens]):
                raise ValueError(
                    "sense_voice and tokens must be provided for sense_voice model type"
                )

        return values


class GroqWhisperASRConfig(I18nMixin):
    api_key: str = Field(..., alias="api_key")
    model: Literal["whisper-large-v3-turbo", "whisper-large-v3"] = Field(
        "whisper-large-v3-turbo", alias="model"
    )
    lang: Optional[str] = Field(None, alias="lang")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_key": Description.from_str("API key for Groq Whisper ASR"),
        "model": Description.from_str("Name of the Groq Whisper model to use"),
        "lang": Description.from_str("Language code (leave empty for auto-detect)"),
    }


# --- Main ASRConfig model ---


class ASRConfig(I18nMixin):
    """
    Configuration for Automatic Speech Recognition.
    """

    asr_model: Literal[
        "Faster-Whisper",
        "WhisperCPP",
        "Whisper",
        "AzureASR",
        "FunASR",
        "GroqWhisperASR",
        "SherpaOnnxASR",
    ] = Field(..., alias="ASR_MODEL")
    azure_asr: Optional[AzureASRConfig] = Field(None, alias="AzureASR")
    faster_whisper: Optional[FasterWhisperConfig] = Field(None, alias="Faster-Whisper")
    whisper_cpp: Optional[WhisperCPPConfig] = Field(None, alias="WhisperCPP")
    whisper: Optional[WhisperConfig] = Field(None, alias="Whisper")
    fun_asr: Optional[FunASRConfig] = Field(None, alias="FunASR")
    groq_whisper_asr: Optional[GroqWhisperASRConfig] = Field(
        None, alias="GroqWhisperASR"
    )
    sherpa_onnx_asr: Optional[SherpaOnnxASRConfig] = Field(None, alias="SherpaOnnxASR")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "asr_model": Description.from_str(
            "Speech-to-text model to use",
            "Options: Faster-Whisper, WhisperCPP, Whisper, AzureASR, FunASR, GroqWhisperASR, SherpaOnnxASR",
        ),
        "azure_asr": Description.from_str("Configuration for Azure ASR"),
        "faster_whisper": Description.from_str("Configuration for Faster Whisper"),
        "whisper_cpp": Description.from_str("Configuration for WhisperCPP"),
        "whisper": Description.from_str("Configuration for Whisper"),
        "fun_asr": Description.from_str("Configuration for FunASR"),
        "groq_whisper_asr": Description.from_str("Configuration for Groq Whisper ASR"),
        "sherpa_onnx_asr": Description.from_str("Configuration for Sherpa Onnx ASR"),
    }

    @model_validator(mode="after")
    def check_asr_config(cls, values: "ASRConfig", info: ValidationInfo):
        asr_model = values.asr_model

        # Only validate the selected ASR model
        if asr_model == "AzureASR" and values.azure_asr is not None:
            values.azure_asr.model_validate(values.azure_asr.model_dump())
        elif asr_model == "Faster-Whisper" and values.faster_whisper is not None:
            values.faster_whisper.model_validate(values.faster_whisper.model_dump())
        elif asr_model == "WhisperCPP" and values.whisper_cpp is not None:
            values.whisper_cpp.model_validate(values.whisper_cpp.model_dump())
        elif asr_model == "Whisper" and values.whisper is not None:
            values.whisper.model_validate(values.whisper.model_dump())
        elif asr_model == "FunASR" and values.fun_asr is not None:
            values.fun_asr.model_validate(values.fun_asr.model_dump())
        elif asr_model == "GroqWhisperASR" and values.groq_whisper_asr is not None:
            values.groq_whisper_asr.model_validate(values.groq_whisper_asr.model_dump())
        elif asr_model == "SherpaOnnxASR" and values.sherpa_onnx_asr is not None:
            values.sherpa_onnx_asr.model_validate(values.sherpa_onnx_asr.model_dump())
        return values
