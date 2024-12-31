# config_manager/asr.py
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Literal, Optional, Dict, ClassVar, Union
from .i18n import I18nMixin, Description, MultiLingualString

class AzureASRConfig(I18nMixin):
    """Configuration for Azure ASR service."""
    
    api_key: str = Field(..., alias="api_key")
    region: Literal["eastus", "westus", "eastasia", "southeastasia"] = Field(..., alias="region")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_key": Description(
            en="API key for Azure ASR service",
            zh="Azure ASR 服务的 API 密钥",
            ui_widget="password",
            ui_options={"autoComplete": "off"}
        ),
        "region": Description(
            en="Azure region (e.g., eastus)",
            zh="Azure 区域（如 eastus）",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "eastus": "East US",
                    "westus": "West US",
                    "eastasia": "East Asia",
                    "southeastasia": "Southeast Asia"
                }
            }
        ),
    }

class FasterWhisperConfig(I18nMixin):
    """Configuration for Faster Whisper ASR."""
    
    model_path: str = Field(..., alias="model_path")
    download_root: str = Field(..., alias="download_root")
    language: Optional[Literal["", "en", "zh", "ja"]] = Field(None, alias="language")
    device: Literal["auto", "cpu", "cuda"] = Field("auto", alias="device")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_path": Description(
            en="Path to the Faster Whisper model",
            zh="Faster Whisper 模型路径",
            ui_widget="text",
            ui_options={"placeholder": "distil-medium.en"}
        ),
        "download_root": Description(
            en="Root directory for downloading models",
            zh="模型下载根目录",
            ui_widget="text",
            ui_options={"placeholder": "models/whisper"}
        ),
        "language": Description(
            en="Language code (e.g., en, zh) or None for auto-detect",
            zh="语言代码（如 en, zh）或留空以自动检测",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "": "Auto Detect",
                    "en": "English",
                    "zh": "Chinese",
                    "ja": "Japanese"
                }
            }
        ),
        "device": Description(
            en="Device to use for inference",
            zh="推理设备",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "auto": "Auto",
                    "cpu": "CPU",
                    "cuda": "CUDA (GPU)"
                }
            }
        ),
    }

class WhisperCPPConfig(I18nMixin):
    """Configuration for WhisperCPP ASR."""
    
    model_name: Literal["tiny", "base", "small", "medium", "large"] = Field(..., alias="model_name")
    model_dir: str = Field(..., alias="model_dir")
    print_realtime: bool = Field(False, alias="print_realtime")
    print_progress: bool = Field(False, alias="print_progress")
    language: Literal["auto", "en", "zh"] = Field("auto", alias="language")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_name": Description(
            en="Name of the Whisper model",
            zh="Whisper 模型名称",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "tiny": "Tiny",
                    "base": "Base",
                    "small": "Small",
                    "medium": "Medium",
                    "large": "Large"
                }
            }
        ),
        "model_dir": Description(
            en="Directory containing Whisper models",
            zh="Whisper 模型目录",
            ui_widget="text",
            ui_options={"placeholder": "models/whisper"}
        ),
        "print_realtime": Description(
            en="Print output in real-time",
            zh="实时打印输出",
            ui_widget="switch"
        ),
        "print_progress": Description(
            en="Print progress information",
            zh="打印进度信息",
            ui_widget="switch"
        ),
        "language": Description(
            en="Language code",
            zh="语言代码",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "auto": "Auto Detect",
                    "en": "English",
                    "zh": "Chinese"
                }
            }
        ),
    }

class WhisperConfig(I18nMixin):
    """Configuration for OpenAI Whisper ASR."""
    
    name: Literal["tiny", "base", "small", "medium", "large"] = Field(..., alias="name")
    download_root: str = Field(..., alias="download_root")
    device: Literal["cpu", "cuda"] = Field("cpu", alias="device")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "name": Description(
            en="Name of the Whisper model",
            zh="Whisper 模型名称",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "tiny": "Tiny",
                    "base": "Base",
                    "small": "Small",
                    "medium": "Medium",
                    "large": "Large"
                }
            }
        ),
        "download_root": Description(
            en="Root directory for downloading models",
            zh="模型下载根目录",
            ui_widget="text",
            ui_options={"placeholder": "models/whisper"}
        ),
        "device": Description(
            en="Device to use for inference",
            zh="推理设备",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "cpu": "CPU",
                    "cuda": "CUDA (GPU)"
                }
            }
        ),
    }

class FunASRConfig(I18nMixin):
    """Configuration for FunASR."""
    
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
        "model_name": Description(
            en="Name of the FunASR model",
            zh="FunASR 模型名称",
            ui_widget="text",
            ui_options={"placeholder": "iic/SenseVoiceSmall"}
        ),
        "vad_model": Description(
            en="Voice Activity Detection model",
            zh="语音活动检测模型",
            ui_widget="text",
            ui_options={"placeholder": "fsmn-vad"}
        ),
        "punc_model": Description(
            en="Punctuation model",
            zh="标点符号模型",
            ui_widget="text",
            ui_options={"placeholder": "ct-punc"}
        ),
        "device": Description(
            en="Device to use for inference",
            zh="推理设备",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "cpu": "CPU",
                    "cuda": "CUDA (GPU)"
                }
            }
        ),
        "disable_update": Description(
            en="Disable checking for FunASR updates on launch",
            zh="启动时禁用 FunASR 更新检查",
            ui_widget="switch"
        ),
        "ncpu": Description(
            en="Number of CPU threads for internal operations",
            zh="内部操作的 CPU 线程数",
            ui_widget="number",
            ui_options={"min": 1, "max": 32}
        ),
        "hub": Description(
            en="Model hub to use",
            zh="使用的模型仓库",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "ms": "ModelScope",
                    "hf": "Hugging Face"
                }
            }
        ),
        "use_itn": Description(
            en="Enable inverse text normalization",
            zh="启用反向文本归一化",
            ui_widget="switch"
        ),
        "language": Description(
            en="Language code",
            zh="语言代码",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "auto": "Auto Detect",
                    "zh": "Chinese",
                    "en": "English"
                }
            }
        ),
    }

class GroqWhisperASRConfig(I18nMixin):
    """Configuration for Groq Whisper ASR."""
    
    api_key: str = Field(..., alias="api_key")
    model: Literal["whisper-large-v3-turbo", "whisper-large-v3"] = Field(
        "whisper-large-v3-turbo", alias="model"
    )
    lang: Optional[Literal["", "en", "zh", "ja"]] = Field(None, alias="lang")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "api_key": Description(
            en="API key for Groq Whisper ASR",
            zh="Groq Whisper ASR 的 API 密钥",
            ui_widget="password",
            ui_options={"autoComplete": "off"}
        ),
        "model": Description(
            en="Name of the Groq Whisper model to use",
            zh="要使用的 Groq Whisper 模型名称",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "whisper-large-v3-turbo": "Whisper Large V3 Turbo",
                    "whisper-large-v3": "Whisper Large V3"
                }
            }
        ),
        "lang": Description(
            en="Language code (leave empty for auto-detect)",
            zh="语言代码（留空以自动检测）",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "": "Auto Detect",
                    "en": "English",
                    "zh": "Chinese",
                    "ja": "Japanese"
                }
            }
        ),
    }

class SherpaOnnxASRConfig(I18nMixin):
    """Configuration for Sherpa Onnx ASR."""

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
    tokens: str = Field(..., alias="tokens")
    num_threads: int = Field(4, alias="num_threads")
    use_itn: bool = Field(True, alias="use_itn")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "model_type": Description(
            en="Type of ASR model to use",
            zh="要使用的 ASR 模型类型",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "transducer": "Transducer",
                    "paraformer": "Paraformer",
                    "nemo_ctc": "NeMo CTC",
                    "wenet_ctc": "WeNet CTC",
                    "whisper": "Whisper",
                    "tdnn_ctc": "TDNN CTC",
                    "sense_voice": "SenseVoice"
                }
            }
        ),
        "encoder": Description(
            en="Path to encoder model (for transducer)",
            zh="编码器模型路径（用于 transducer）",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/encoder.onnx",
                "accept": ".onnx"
            }
        ),
        "decoder": Description(
            en="Path to decoder model (for transducer)",
            zh="解码器模型路径（用于 transducer）",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/decoder.onnx",
                "accept": ".onnx"
            }
        ),
        "joiner": Description(
            en="Path to joiner model (for transducer)",
            zh="连接器模型路径（用于 transducer）",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/joiner.onnx",
                "accept": ".onnx"
            }
        ),
        "paraformer": Description(
            en="Path to paraformer model",
            zh="Paraformer 模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/model.onnx",
                "accept": ".onnx"
            }
        ),
        "nemo_ctc": Description(
            en="Path to NeMo CTC model",
            zh="NeMo CTC 模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/model.onnx",
                "accept": ".onnx"
            }
        ),
        "wenet_ctc": Description(
            en="Path to WeNet CTC model",
            zh="WeNet CTC 模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/model.onnx",
                "accept": ".onnx"
            }
        ),
        "tdnn_model": Description(
            en="Path to TDNN model",
            zh="TDNN 模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/model.onnx",
                "accept": ".onnx"
            }
        ),
        "whisper_encoder": Description(
            en="Path to Whisper encoder model",
            zh="Whisper 编码器模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/encoder.onnx",
                "accept": ".onnx"
            }
        ),
        "whisper_decoder": Description(
            en="Path to Whisper decoder model",
            zh="Whisper 解码器模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/decoder.onnx",
                "accept": ".onnx"
            }
        ),
        "sense_voice": Description(
            en="Path to SenseVoice model",
            zh="SenseVoice 模型路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.onnx",
                "accept": ".onnx"
            }
        ),
        "tokens": Description(
            en="Path to tokens file",
            zh="词元文件路径",
            ui_widget="file",
            ui_options={
                "placeholder": "path/to/tokens.txt",
                "accept": ".txt"
            }
        ),
        "num_threads": Description(
            en="Number of computation threads",
            zh="计算线程数",
            ui_widget="number",
            ui_options={
                "min": 1,
                "max": 32,
                "step": 1
            }
        ),
        "use_itn": Description(
            en="Enable inverse text normalization",
            zh="启用反向文本归一化",
            ui_widget="switch"
        ),
    }

    @model_validator(mode='after')
    def check_model_paths(cls, values: "SherpaOnnxASRConfig", info: ValidationInfo):
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

class ASRConfig(I18nMixin):
    """Configuration for Automatic Speech Recognition."""
    
    asr_model: Literal[
        "faster_whisper",
        "whisper_cpp",
        "whisper",
        "azure_asr",
        "fun_asr",
        "groq_whisper_asr",
        "sherpa_onnx_asr",
    ] = Field(..., alias="asr_model")
    azure_asr: Optional[AzureASRConfig] = Field(None, alias="azure_asr")
    faster_whisper: Optional[FasterWhisperConfig] = Field(None, alias="faster_whisper")
    whisper_cpp: Optional[WhisperCPPConfig] = Field(None, alias="whisper_cpp")
    whisper: Optional[WhisperConfig] = Field(None, alias="whisper")
    fun_asr: Optional[FunASRConfig] = Field(None, alias="fun_asr")
    groq_whisper_asr: Optional[GroqWhisperASRConfig] = Field(None, alias="groq_whisper_asr")
    sherpa_onnx_asr: Optional[SherpaOnnxASRConfig] = Field(None, alias="sherpa_onnx_asr")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "asr_model": Description(
            en="Speech-to-text model to use",
            zh="要使用的语音识别模型",
            ui_widget="select",
            ui_options={
                "enumNames": {
                    "faster_whisper": "Faster Whisper",
                    "whisper_cpp": "Whisper CPP",
                    "whisper": "OpenAI Whisper",
                    "azure_asr": "Azure ASR",
                    "fun_asr": "FunASR",
                    "groq_whisper_asr": "Groq Whisper",
                    "sherpa_onnx_asr": "Sherpa Onnx ASR"
                }
            }
        ),
        "azure_asr": Description(
            en="Configuration for Azure ASR",
            zh="Azure ASR 配置"
        ),
        "faster_whisper": Description(
            en="Configuration for Faster Whisper",
            zh="Faster Whisper 配置"
        ),
        "whisper_cpp": Description(
            en="Configuration for WhisperCPP",
            zh="WhisperCPP 配置"
        ),
        "whisper": Description(
            en="Configuration for Whisper",
            zh="Whisper 配置"
        ),
        "fun_asr": Description(
            en="Configuration for FunASR",
            zh="FunASR 配置"
        ),
        "groq_whisper_asr": Description(
            en="Configuration for Groq Whisper ASR",
            zh="Groq Whisper ASR 配置"
        ),
        "sherpa_onnx_asr": Description(
            en="Configuration for Sherpa Onnx ASR",
            zh="Sherpa Onnx ASR 配置"
        ),
    }

    @model_validator(mode='after')
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
