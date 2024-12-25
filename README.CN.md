# Open-LLM-VTuber

(Gemini 1.5 Pro 翻译, 文档写不过来了... 起码Gemini翻译的应该会比浏览器翻译要好一些)

[![GitHub Release](https://img.shields.io/github/v/release/t41372/Open-LLM-VTuber)](https://github.com/t41372/Open-LLM-VTuber/releases)
[![license](https://img.shields.io/github/license/t41372/Open-LLM-VTuber)](https://github.com/t41372/Open-LLM-VTuber/blob/master/LICENSE)
[![](https://img.shields.io/badge/t41372%2FOpen--LLM--VTuber-%25230db7ed.svg?logo=docker&logoColor=blue&labelColor=white&color=blue)](https://hub.docker.com/r/t41372/open-llm-vtuber)
[![](https://img.shields.io/badge/todo_list-GitHub_Project-blue)](https://github.com/users/t41372/projects/1/views/1)

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/yi.ting) [![](https://dcbadge.limes.pink/api/server/3UDA8YFDXx)](https://discord.gg/3UDA8YFDXx) <- (可点击的链接)

(QQ群: 792615362）<- 比 Discord 群活跃得多，群成员超过 700 人，且大多数贡献者都在群里。
> 常见问题文档 (中文): https://docs.qq.com/doc/DTHR6WkZ3aU9JcXpy
>
> 用户调查问卷: https://forms.gle/w6Y6PiHTZr1nzbtWA
>
> 调查问卷(中文)(现在不用登录了): https://wj.qq.com/s2/16150415/f50a/



> :warning: 本项目尚处于早期阶段，并且正在**积极开发中**。功能不稳定，代码杂乱，会有重大变更。此阶段的主要目标是使用易于集成的技术构建一个最小可行原型。

> :warning: 本项目的安装过程**并不容易**。如果您需要帮助或想获取有关此项目的更新信息，请加入 Discord 服务器或 QQ 群。

> :warning: 如果您想在服务器上运行此程序并通过笔记本电脑远程访问，前端的麦克风仅在安全环境（即 https 或 localhost）下才能启动。请参阅 [MDN Web 文档](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)。因此，您应该配置 https 反向代理以访问远程机器（非 localhost）上的页面。

> 如果您认为README和文档超级混乱，您是对的！我们计划对文档进行全面的重构。与此同时，如果您懂中文 (我猜你看懂，别问我怎么知道的)，可以观看安装视频。


### ❓ 这个项目是做什么的？

Open-LLM-VTuber 允许您通过语音（无需动手）与任何本地 LLM 进行对话（并随时打断！），并配有 Live2D 说话头像。LLM 推理后端、语音识别和语音合成器都设计为可更换的。该项目可以配置为在 macOS、Linux 和 Windows 上离线运行。也支持在线 LLM/ASR/TTS 选项。

可以通过配置 MemGPT 实现长期记忆，以实现永久聊天、无限* 上下文长度和外部数据源。

该项目最初是为了尝试使用开源替代方案重现闭源 AI VTuber `neuro-sama`，这些替代方案可以在 Windows 以外的平台上离线运行。

<img width="500" alt="demo-image" src="https://github.com/t41372/Open-LLM-VTuber/assets/36402030/fa363492-7c01-47d8-915f-f12a3a95942c"/>

### 演示

英语演示：

https://github.com/user-attachments/assets/f13b2f8e-160c-4e59-9bdb-9cfb6e57aca9

英语演示：
[YouTube](https://youtu.be/gJuPM_2qEZc)

中文演示：

[BiliBili](https://www.bilibili.com/video/BV1krHUeRE98/), [YouTube](https://youtu.be/cb5anPTNklw)

### 为什么选择本项目而不是 GitHub 上其他类似项目？

- 它可以在 macOS 上运行
  - 许多现有的解决方案使用 VTube Studio 显示 Live2D 模型，并通过将桌面内部音频路由到 VTube Studio 并用其控制嘴唇来实现唇形同步。然而，在 macOS 上，没有简单的方法可以让 VTuber Studio 侦听桌面上的内部音频。
  - 许多现有的解决方案缺乏对 macOS 上 GPU 加速的支持，这使得它们在 Mac 上运行缓慢。
- 本项目支持 [MemGPT](https://github.com/cpacker/MemGPT) 以实现永久聊天。聊天机器人会记住您说过的话。
- 如果您愿意，数据不会离开您的计算机
  - 您可以选择本地 LLM/语音识别/语音合成解决方案；一切都可以离线运行。已在 macOS 上测试。
- 您可以随时用语音打断 LLM，而无需佩戴耳机。

### 基本功能

- [x] 通过语音与任何 LLM 聊天
- [x] 随时用语音打断 LLM
- [x] 选择您自己的 LLM 后端
- [x] 选择您自己的语音识别和文本转语音提供商
- [x] 长期记忆
- [x] Live2D 前端

### 目标平台

- macOS
- Linux
- Windows

### 近期功能更新

查看 GitHub Release 获取更新说明。

## 已实现的功能

- 通过语音与 LLM 交谈。离线。
- ~~对聊天记录进行 RAG~~ *(暂时移除)*

目前支持的 LLM 后端
- 任何与 OpenAI-API 兼容的后端，例如 Ollama、Groq、LM Studio、OpenAI 等。
- Claude
- 本项目内的 llama.cpp 本地推理
- MemGPT (已损坏)
- Mem0 (不太好)

目前支持的语音识别后端
- [FunASR](https://github.com/modelscope/FunASR)，支持 [SenseVoiceSmall](https://github.com/FunAudioLLM/SenseVoice) 和许多其他模型。（~~本地~~ 当前需要互联网连接进行加载。本地计算）
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (本地)
- [Whisper-CPP](https://github.com/ggerganov/whisper.cpp) 使用 Python 绑定 [pywhispercpp](https://github.com/abdeladim-s/pywhispercpp) (本地，可以配置 mac GPU 加速)
- [Whisper](https://github.com/openai/whisper) (本地)
- [Groq Whisper](https://groq.com/) (需要 API 密钥)。这是一个托管的 Whisper 端点。它速度很快，并且每天都有慷慨的免费限额。
- [Azure 语音识别](https://azure.microsoft.com/en-us/products/ai-services/speech-to-text) (需要 API 密钥)
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) (本地，快速，支持各种模型，包括 transducer、Paraformer、NeMo CTC、WeNet CTC、Whisper、TDNN CTC 和 SenseVoice 模型。)
- 默认情况下将使用服务器终端中的麦克风。您可以在 `conf.yaml` 中更改设置 `MIC_IN_BROWSER`，将麦克风（和语音激活检测）移动到浏览器（目前以延迟为代价）。如果您在不同的机器上或在 VM 或 docker 内运行后端，您可能希望使用客户端（浏览器）上的麦克风，而不是服务器上的麦克风。

目前支持的文本转语音后端
- [py3-tts](https://github.com/thevickypedia/py3-tts) (本地，它使用您系统的默认 TTS 引擎)
- [meloTTS](https://github.com/myshell-ai/MeloTTS) (本地，快速)
- [Coqui-TTS](https://github.com/idiap/coqui-ai-TTS) (本地，速度取决于您运行的模型。)
- [bark](https://github.com/suno-ai/bark) (本地，非常消耗资源)
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) (本地，非常消耗资源)
- [xTTSv2](https://github.com/daswer123/xtts-api-server) (本地，非常消耗资源)
- [Edge TTS](https://github.com/rany2/edge-tts) (在线，无需 API 密钥)
- [Azure 文本转语音](https://azure.microsoft.com/en-us/products/ai-services/text-to-speech) (在线，需要 API 密钥)
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) (本地，快速，支持各种模型。对于英语，建议使用 piper 模型。对于纯中文，请考虑使用 [sherpa-onnx-vits-zh-ll.tar.bz2](https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-vits-zh-ll.tar.bz2)。对于中英文混合，可以使用 [vits-melo-tts-zh_en.tar.bz2](https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2)，尽管英语发音可能不太理想。)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) (请查看[此处的文档](https://docs.qq.com/doc/DTHR6WkZ3aU9JcXpy))

快速文本合成
- 句子一到达就进行合成，因此无需等待整个 LLM 响应。
- 采用多线程的生产者-消费者模型：音频将在后台持续合成。每当新音频准备好时，它们将逐个播放。音频播放器不会阻塞音频合成器。

Live2D 说话头像
- 使用 `config.yaml` 更改 Live2D 模型 (模型需要在 model_dict.json 中列出)
- 加载本地 Live2D 模型。查看 `doc/live2d.md` 获取文档。
- 使用 LLM 响应中的表情关键词来控制面部表情，因此无需额外的模型进行情绪检测。表情关键词会自动加载到系统提示中，并从语音合成输出中排除。

live2d 技术细节
- 使用 [guansss/pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) 在*浏览器*中显示 live2d 模型
- 使用 WebSocket 在服务器和前端之间控制面部表情和说话状态
- 所有必需的软件包都在本地可用，因此前端可以离线工作。
- 您可以从 URL 或存储在 `live2d-models` 目录中的本地模型加载 live2d 模型。默认的 `shizuku-local` 存储在本地并且可以离线工作。如果 model_dict.json 中模型的 URL 属性是一个 URL，而不是以 `/live2d-models` 开头的路径，则每次打开前端时都需要从指定的 URL 获取它们。阅读 `doc/live2d.md` 获取有关从本地加载您的 live2D 模型的文档。
- 运行 `server.py` 来运行 WebSocket 通信服务器，打开 `./static` 文件夹中的 `index.html` 来打开前端，并运行 ~~`launch.py`~~ `main.py` 来运行用于 LLM/ASR/TTS 处理的后端。

## 快速开始

如果您说中文，这里有两个安装视频供您参考。
- (首选 🎉) `v0.4.3` [为 Windows 用户提供自动安装脚本的完整教程](https://www.bilibili.com/video/BV1UDz4YcEr8/)
- `v0.2.4` [在 macOS 上手动安装教程](https://www.bilibili.com/video/BV1GYSrYKE8i/)

如果您不说中文，祝您好运。如果您创建了其他语言的教程，请告诉我，我可以把它放在这里。

> **新的安装说明正在[此处](https://github.com/t41372/Open-LLM-VTuber/wiki)创建**

### 一键启动脚本
`v0.4.0` 中添加了一个新的快速启动脚本（实验性）。
此脚本允许您运行此项目，而无需（过多）担心依赖项。
此脚本唯一需要的是 Python、良好的互联网连接和足够的磁盘空间。

此脚本将执行以下操作：
- 在项目目录中下载 miniconda
- 在项目目录中创建一个 conda 环境
- 安装 `FunASR` + `edgeTTS` 配置所需的所有依赖项（您仍然需要获取 ollama 或某些与 OpenAI 兼容的后端）
- 在 conda 环境中运行此项目

使用 `python start_webui.py` 运行脚本。请注意，如果您决定使用自动安装脚本，则应始终使用 `start_webui.py` 作为入口点，因为 `server.py` 不会为您启动 conda 环境。

另请注意，如果您想安装其他依赖项，您需要先运行 `python activate_conda.py` 进入自动配置的 conda 环境。

## 手动安装

一般来说，运行该项目需要四个步骤：
1. 基础设置
2. 获取大语言模型 (LLM)
3. 获取语音合成 (TTS)
4. 获取语音识别 (ASR)

### 要求:
- ffmpeg
- Python >= 3.10, < 3.13 (3.13 目前尚不兼容)

克隆此仓库。

强烈建议使用虚拟 Python 环境，如 conda 或 venv！（因为依赖项非常混乱！）

在终端中运行以下命令以安装基本依赖项。

~~~shell
pip install -r requirements.txt # 在项目目录中运行
# 根据以下说明安装语音识别和语音合成依赖项
~~~

编辑 `conf.yaml` 文件进行配置。您可以参考演示视频中使用的配置。

一旦 live2D 模型出现在屏幕上，就可以开始与它对话了。

~~如果您不需要 live2d，可以使用 Python 运行 `main.py` 进入命令行模式。~~ (命令行模式现已弃用，并将在 `v1.0.0` 中删除。如果仍有人需要命令行模式，将来可能会制作一个命令行客户端，但当前的架构很快就会重构)

首次启动时将下载一些模型，这可能需要互联网连接并且可能需要一些时间。



### 更新
🎉 `v0.3.0` 中添加了一个新的实验性更新脚本。运行 `python upgrade.py` 以更新到最新版本。

如果您已编辑配置文件 `conf.yaml`，请先备份，然后再更新仓库。
或者重新克隆仓库，并确保迁移您的配置。由于该项目仍处于早期阶段，配置文件有时会发生变化。更新程序时请务必小心。

## 配置 LLM

### 兼容 OpenAI 的 LLM，例如 Ollama、LM Studio、vLLM、groq、智谱、Gemini、OpenAI 等
在 `conf.yaml` 文件中将 `LLM_PROVIDER` 选项设置为 `ollama` 并填写设置。

如果您使用官方 OpenAI API，则 base_url 为 `https://api.openai.com/v1`。

### Claude

在 https://github.com/t41372/Open-LLM-VTuber/pull/35 中，`v0.3.1` 版本添加了对 Claude 的支持。

将 `LLM_PROVIDER` 更改为 `claude` 并在 `claude` 下完成设置。

### LLama CPP (在 `v0.5.0-alpha.2` 中添加)

提供了一种**在**本项目中运行 LLM 的方法，无需任何外部工具（如 Ollama）。您只需要一个 `.gguf` 模型文件。

#### 要求

根据 [项目仓库](https://github.com/abetlen/llama-cpp-python)

要求：

- Python 3.8+
- C 编译器
  - Linux：gcc 或 clang
  - Windows：Visual Studio 或 MinGW
  - MacOS：Xcode

这还将从源代码构建 `llama.cpp` 并将其与此 Python 包一起安装。

如果失败，请在 `pip install` 命令中添加 `--verbose` 以查看完整的 cmake 构建日志。



### 安装

在[此处](https://github.com/abetlen/llama-cpp-python?tab=readme-ov-file#supported-backends)查找适用于您平台的 `pip install llama-cpp-python` 命令。

例如：

如果您使用 Nvidia GPU，请运行以下命令。

`CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python`

如果您使用 Apple Silicon Mac（像我一样），请执行以下操作：

`CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python`

如果您使用支持 ROCm 的 AMD GPU：

`CMAKE_ARGS="-DGGML_HIPBLAS=on" pip install llama-cpp-python`

如果您想使用 CPU (OpenBlas)：

`CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python`



有关更多选项，请查看[此处](https://github.com/abetlen/llama-cpp-python?tab=readme-ov-file#supported-backends)。





### MemGPT (已损坏，可能会被移除而不是修复)

> :warning: MemGPT 已更名为 Letta，并且他们更改了 API。目前，本项目中 MemGPT 的集成尚未更新为最新更改，因此集成已损坏。
> 由于 MemGPT（或现在的 Letta）对于本地 LLM 来说非常缓慢且不稳定，因此可能不会修复。计划采用新的长期记忆解决方案。

但是，您仍然可以获取旧版本的 MemGPT 并试用。这是文档。

> MemGPT 集成非常具有实验性，需要进行大量设置。此外，MemGPT 需要具有大量 token 占用空间的强大 LLM（大于 7b 且量化高于 Q5），这意味着它要慢得多。
> 不过，MemGPT 确实有自己的免费 LLM 端点。您可以使用它进行测试。查看他们的文档。

该项目可以使用 [MemGPT](https://github.com/cpacker/MemGPT) 作为其 LLM 后端。MemGPT 使 LLM 具备长期记忆能力。

要使用 MemGPT，您需要配置并运行 MemGPT 服务器。您可以使用 `pip` 或 `docker` 安装它，也可以在不同的机器上运行它。查看他们的 [GitHub 仓库](https://github.com/cpacker/MemGPT) 和 [官方文档](https://memgpt.readme.io/docs/index)。

> :warning:
> 我建议您将 MemGPT 安装在单独的 Python 虚拟环境或 docker 中，因为当前该项目和 MemGPT 之间存在依赖冲突（似乎是在 fast API 上）。您可以查看此问题 [Can you please upgrade typer version in your dependancies #1382](https://github.com/cpacker/MemGPT/issues/1382)。



以下是一个清单：
- 安装 memgpt
- 配置 memgpt
- 使用 `memgpt server` 命令运行 `memgpt`。请记住在启动 Open-LLM-VTuber 之前运行服务器。
- 通过其 cli 或 Web UI 设置代理。使用 Live2D 表达式提示和您要使用的表达式关键字（在 `model_dict.json` 中查找）将您的系统提示添加到 MemGPT 中
- 将 `服务器管理员密码` 和 `代理 ID` 复制到 `./llm/memgpt_config.yaml` 中。*顺便说一下，`代理 ID` 不是代理的名称*。
- 在 `conf.yaml` 中将 `LLM_PROVIDER` 设置为 `memgpt`。
- 请记住，如果您使用 `memgpt`，`conf.yaml` 中所有与 LLM 相关的配置都将被忽略，因为 `memgpt` 不是那样工作的。



### Mem0 (事实证明它不太适合我们的用例，但代码在这里...)

另一种长期记忆解决方案。仍在开发中。高度实验性。

优点

- 与 MemGPT 相比，它更容易设置
- 它比 MemGPT 快一点（但仍需要处理更多的 LLM token）

缺点

- 它会记住您的偏好和想法，仅此而已。它不记得 LLM 说过什么。
- 它并不总是将内容放入内存。
- 它有时会记住错误的内容
- 它需要一个具有非常好的函数调用能力的 LLM，这对于较小的模型来说非常困难
- 

## 安装语音识别 (ASR)
编辑 `conf.yaml` 中的 ASR_MODEL 设置以更改提供程序。

以下是您可以选择的语音识别选项：

`sherpa-onnx` (本地，运行速度非常快) (在 https://github.com/t41372/Open-LLM-VTuber/pull/50 的 `v0.5.0-alpha.1` 中添加)
- 使用 `pip install sherpa-onnx` 安装。(~20MB)
- 从 [sherpa-onnx ASR models](https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models) 下载您需要的模型。
- 参考仓库中的 `config_alts` 获取配置示例，并相应地修改 `conf.yaml` 中的模型路径。
- 它提供了出色的性能，并且比 FunASR 轻得多。

`FunASR` (~~本地~~) (即使在 CPU 上也能非常快速地运行。不确定他们是如何做到的)
- [FunASR](https://github.com/modelscope/FunASR?tab=readme-ov-file) 是 ModelScope 的一个基础端到端语音识别工具包，可以运行许多 ASR 模型。来自阿里巴巴集团 [FunAudioLLM](https://github.com/FunAudioLLM/SenseVoice) 的 SenseVoiceSmall 的结果和速度都相当不错。
- 使用 `pip install -U funasr modelscope huggingface_hub` 安装。此外，请确保您已安装 torch (torch>=1.13) 和 torchaudio。使用 `pip install torch torchaudio onnx` 安装它们（FunASR 现在也需要 `onnx`）
- 即使模型在本地可用，启动时也需要互联网连接。请参阅 https://github.com/modelscope/FunASR/issues/1897

`Faster-Whisper` (本地)
- Whisper，但速度更快。在 macOS 上，它仅在 CPU 上运行，速度不是很快，但易于使用。
- 对于 Nvidia GPU 用户，要使用 GPU 加速，您需要安装以下 NVIDIA 库：
  - [cuBLAS for CUDA 12](https://developer.nvidia.com/cublas)
  - [cuDNN 8 for CUDA 12](https://developer.nvidia.com/cudnn)
- 或者，如果您不需要速度，可以在 `conf.yaml` 中将 `Faster-Whisper` 下的 `device` 设置为 `cpu` 以减少麻烦。

`WhisperCPP` (本地) (如果在 Mac 上正确配置，则运行速度非常快)
- 如果您使用的是 Mac，请阅读以下说明以设置支持 coreML 的 WhisperCPP。如果您想使用 CPU 或 Nvidia GPU，请运行 `pip install pywhispercpp` 安装该软件包。
- Whisper cpp python 绑定。它可以通过配置在 coreML 上运行，这使得它在 macOS 上非常快。
- 在 CPU 或 Nvidia GPU 上，它可能比 Faster-Whisper 慢

WhisperCPP coreML 配置：
- 如果您已经安装了原始的 `pywhispercpp`，请将其卸载。我们正在构建该软件包。
- 使用 Python 运行 `install_coreml_whisper.py` 以自动为您克隆和构建支持 coreML 的 `pywhispercpp`。
- 准备适当的 coreML 模型。
  - 您可以根据 Whisper.cpp 仓库的文档将模型转换为 coreml
  - ...或者您可以找到一些 [神奇的 huggingface 仓库](https://huggingface.co/chidiwilliams/whisper.cpp-coreml/tree/main)，它们碰巧有这些转换后的模型。只需记住解压缩它们。如果程序无法加载模型，它将产生分段错误。
  - 您不需要在 `conf.yaml` 中的模型名称中包含那些奇怪的前缀。例如，如果 coreML 模型的名称类似于 `ggml-base-encoder.mlmodelc`，只需将 `base` 放入 `conf.yaml` 中 `WhisperCPP` 设置下的 `model_name` 中。

`Whisper` (本地)
- OpenAI 的原始 Whisper。使用 `pip install -U openai-whisper` 安装
- 最慢的一个。添加它是为了试验看看它是否可以利用 macOS GPU。它没有。

`GroqWhisperASR` (在线，需要 API 密钥)

- Groq 的 Whisper 端点。它非常快，并且每天都有很多免费使用次数。它已预安装。从 [groq](https://console.groq.com/keys) 获取 API 密钥并将其添加到 `conf.yaml` 中的 GroqWhisper 设置中。
- 需要 API 密钥和互联网连接。

`AzureASR` (在线，需要 API 密钥)

- Azure 语音识别。使用 `pip install azure-cognitiveservices-speech` 安装。
- 需要 API 密钥和互联网连接。
- **⚠️ ‼️ `api_key.py` 在 `v0.2.5` 中已弃用。请在 `conf.yaml` 中设置 API 密钥。**

## 安装语音合成 (text to speech) (TTS)
安装相应的软件包并使用 `conf.yaml` 中的 `TTS_MODEL` 选项将其打开。

`sherpa-onnx` (本地) (在 https://github.com/t41372/Open-LLM-VTuber/pull/50 的 `v0.5.0-alpha.1` 中添加)
- 使用 `pip install sherpa-onnx` 安装。
- 从 [sherpa-onnx TTS models](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models) 下载您需要的模型。
- 参考仓库中的 `config_alts` 获取配置示例，并相应地修改 `conf.yaml` 中的模型路径。

`pyttsx3TTS` (本地，快速)
- 使用命令 `pip install py3-tts` 安装。
- 此软件包将使用您系统上的默认 TTS 引擎。它在 Windows 上使用 `sapi5`，在 Mac 上使用 `nsss`，在其它平台上使用 `espeak`。
- 使用 `py3-tts` 而不是更著名的 `pyttsx3`，因为 `pyttsx3` 似乎无人维护，并且我无法让最新版本的 `pyttsx3` 工作。

`meloTTS` (本地，快速)
- 我建议使用 `sherpa-onnx` 进行 MeloTTS 推理。此处的 MeloTTS 实现**非常难以**安装。
- 根据其 [文档](https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md) 安装 MeloTTS（不要通过 docker 安装）（克隆仓库的一个好地方是子模块文件夹，但您可以将其放在任何您想要的位置）。如果您遇到与 `mecab-python` 相关的问题，请尝试此 [fork](https://github.com/polm/MeloTTS)（截至 2024 年 7 月 16 日尚未合并到主分支）。
- 它不是最好的，但它绝对比 pyttsx3TTS 好，并且在我的 mac 上速度非常快。如果我无法访问互联网，我会暂时选择这个（如果我有互联网，我会使用 edgeTTS）。

`coquiTTS` (本地，速度可能快也可能慢，具体取决于您运行的模型)

- 似乎易于安装
- 使用命令 `pip install "coqui-tts[languages]" ` 安装
- 支持许多不同的 TTS 模型。使用 `tts --list_models` 命令列出所有支持的模型。
- 默认模型是仅限英语的模型。
- 使用 `tts_models/zh-CN/baker/tacotron2-DDC-GST` 作为中文模型。（但一致性很奇怪...）
- 如果您找到了好用的模型，请告诉我！模型太多了，我甚至不知道从哪里开始...

`GPTSoVITS` (本地，速度还行) (在 https://github.com/t41372/Open-LLM-VTuber/pull/40 的 `v0.4.0` 中添加)
- 请查看 [此文档](https://docs.qq.com/doc/DTHR6WkZ3aU9JcXpy) 以获取安装说明。

`barkTTS` (本地，慢)

- 使用此命令 `pip install git+https://github.com/suno-ai/bark.git` 安装 pip 软件包并在 `conf.yaml` 中将其打开。
- 所需的模型将在首次启动时下载。

`cosyvoiceTTS` (本地，慢)
- 根据其文档配置 [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) 并启动 WebUI 演示。
- 编辑 `conf.yaml` 以匹配您所需的配置。查看其 WebUI 和 WebUI 上的 API 文档，以了解 `conf.yaml` 中 `cosyvoiceTTS` 设置下配置的含义。

`xTTSv2` (本地，慢) (在 https://github.com/t41372/Open-LLM-VTuber/pull/23 的 `v0.2.4` 中添加)
- 建议使用 xtts-api-server，它有清晰的 API 文档并且相对容易部署。

`edgeTTS` (在线，无需 API 密钥)
- 使用此命令 `pip install edge-tts` 安装 pip 软件包并在 `conf.yaml` 中将其打开。
- 听起来不错。运行速度很快。
- 使用 edge tts 时请记住连接到互联网。

`fishAPITTS` (在线，需要 API 密钥) `(在 v0.3.0-beta 中添加)`

- 使用 `pip install fish-audio-sdk` 安装
- 注册一个帐户，获取一个 API 密钥，找到您想要使用的声音，然后在 [Fish Audio](https://fish.audio/) 上复制参考 ID。
- 在 `conf.yaml` 文件中，将 `TTS_MODEL` 设置为 `fishAPITTS`，并在 `fishAPITTS` 设置下，设置 `api_key` 和 `reference_id`。

`AzureTTS` (在线，需要 API 密钥) (这与 neuro-sama 使用的 TTS 完全相同)

- 使用命令 `pip install azure-cognitiveservices-speech` 安装 Azure SDK。
- 从 Azure 获取 API 密钥（用于文本转语音）。
- **⚠️ ‼️ `api_key.py` 在 `v0.2.5` 中已弃用。请在 `conf.yaml` 中设置 API 密钥。**
- `conf.yaml` 中的默认设置是 neuro-sama 使用的声音。



如果您使用的是 macOS，则需要启用终端模拟器的麦克风权限（您在终端中运行此程序，对吧？请为您的终端启用麦克风权限）。如果您未能这样做，语音识别将无法听到您的声音，因为它没有使用您的麦克风的权限。


5. 打开 localhost:12393 进行测试

# 🎉🎉🎉 相关项目

[ylxmf2005/LLM-Live2D-Desktop-Assitant](https://github.com/ylxmf2005/LLM-Live2D-Desktop-Assitant)
- 您的 Live2D 桌面助手由 LLM 提供支持！适用于 Windows 和 MacOS，它可以感知您的屏幕，检索剪贴板内容，并使用独特的声音响应语音命令。具有语音唤醒、唱歌功能和完整的计算机控制，可与您喜欢的角色进行无缝交互。



# 🛠️ 开发
（本项目处于积极的原型阶段，因此很多事情都会发生变化）

本项目中使用的一些缩写：

- LLM：大型语言模型
- TTS：文本转语音、语音合成、声音合成
- ASR：自动语音识别、语音识别、语音转文本、STT
- VAD：语音激活检测

### 关于采样率

您可以假设整个项目中的采样率为 `16000`。
前端将采样率为 `16000` 的 `Float32Array` 数据块流式传输到后端。

### 添加对新 TTS 提供程序的支持
1. 实现 `tts/tts_interface.py` 中定义的 `TTSInterface`。
1. 将您的新 TTS 提供程序添加到 `tts_factory`：实例化并返回 tts 实例的工厂。
1. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递给您的 TTSEngine 的构造函数。

### 添加对新语音识别提供程序的支持
1. 实现 `asr/asr_interface.py` 中定义的 `ASRInterface`。
2. 将您的新 ASR 提供程序添加到 `asr_factory`：实例化并返回 ASR 实例的工厂。
3. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递给您的类的构造函数。

### 添加对新 LLM 提供程序的支持
1. 实现 `llm/llm_interface.py` 中定义的 `LLMInterface`。
2. 将您的新 LLM 提供程序添加到 `llm_factory`：实例化并返回 LLM 实例的工厂。
3. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递给您的类的构造函数。

### 添加对新翻译提供程序的支持
1. 实现 `translate/translate_interface.py` 中定义的 `TranslateInterface`。
1. 将您的新 TTS 提供程序添加到 `translate_factory`：实例化并返回 tts 实例的工厂。
1. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递给您的翻译器的构造函数。

# 致谢
我从中学习的优秀项目

- https://github.com/dnhkng/GlaDOS
- https://github.com/SchwabischesBauernbrot/unsuperior-ai-waifu
- https://codepen.io/guansss/pen/oNzoNoz
- https://github.com/Ikaros-521/AI-Vtuber
- https://github.com/zixiiu/Digital_Life_Server



## Star 历史

[![Star 历史图表](https://api.star-history.com/svg?repos=t41372/open-llm-vtuber&type=Date)](https://star-history.com/#t41372/open-llm-vtuber&Date)