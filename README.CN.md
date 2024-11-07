# Open-LLM-VTuber



[![GitHub 版本](https://img.shields.io/github/v/release/t41372/Open-LLM-VTuber)](https://github.com/t41372/Open-LLM-VTuber/releases) 
[![许可证](https://img.shields.io/github/license/t41372/Open-LLM-VTuber)](https://github.com/t41372/Open-LLM-VTuber/blob/master/LICENSE) 
[![](https://img.shields.io/badge/t41372%2FOpen--LLM--VTuber-%25230db7ed.svg?logo=docker&logoColor=blue&labelColor=white&color=blue)](https://hub.docker.com/r/t41372/open-llm-vtuber) 
[![](https://img.shields.io/badge/todo_list-GitHub_Project-blue)](https://github.com/users/t41372/projects/1/views/1)

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/yi.ting) [![](https://dcbadge.limes.pink/api/server/3UDA8YFDXx)](https://discord.gg/3UDA8YFDXx)


(QQ群: 792615362）

> 用户调查：https://forms.gle/w6Y6PiHTZr1nzbtWA
>
> 调查问卷(中文): https://docs.qq.com/form/page/DTERQRkJMRWNiSldI


> :warning: **如果您正在从没有语音打断功能的旧版本更新，请阅读此内容**:
> 最新版本更改了打开Live2D服务器和后端的方式：`server.py`现在启动它需要的一切（除了浏览器）。要使用Live2D和浏览器运行，请启动`server.py`并在浏览器中打开网页。您不再需要使用`server.py`运行`main.py`。运行`server.py`假定使用浏览器进入Live2D模式，运行`main.py`假定不使用浏览器进入非Live2D模式。此外，由于后端的变化，配置文件中的选项`MIC-IN-BROWSER`和`LIVE2D`不再有任何作用，并且已被弃用。

> :warning: 该项目处于早期阶段，目前正在**积极开发中**。功能不稳定，代码混乱，并且会出现重大更改。此阶段的主要目标是使用易于集成的技术构建最小可行原型。

> :warning: 此项目目前**在Windows上存在很多问题**。理论上，它应该都能工作，但是许多使用Windows的人在许多依赖项上都遇到了很多问题。我将来可能会修复这些功能，但Windows支持目前需要测试和调试。如果您有Mac或Linux机器，请暂时使用它们。如果您需要帮助或获取有关此项目的更新，请加入Discord服务器。

> :warning: 如果您想在服务器上运行此程序并在笔记本电脑上远程访问它，前端的麦克风将仅在安全上下文中启动（即https或localhost）。请参阅 [MDN Web文档](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)。因此，如果您想在远程机器（非本地主机）上访问该页面，您可能需要使用反向代理配置https。


### 这是什么项目？


Open-LLM-VTuber 允许您通过语音（免提）与本地任何大型语言模型 (LLM) 对话（并打断！），并带有 Live2D 动画面部。LLM 推理后端、语音识别和语音合成器都设计为可交换的。此项目可以配置为在 macOS、Linux 和 Windows 上离线运行。也支持在线 LLM/ASR/TTS 选项。

可以使用 MemGPT 配置长期记忆，以实现永久聊天、无限*上下文长度和外部数据源。

这个项目最初是为了尝试使用可以在Windows以外的平台上离线运行的开源替代方案来重建闭源 AI 虚拟主播 `neuro-sama`。


<img width="500" alt="demo-image" src="https://github.com/t41372/Open-LLM-VTuber/assets/36402030/fa363492-7c01-47d8-915f-f12a3a95942c"/>



### 演示

英文演示：

https://github.com/user-attachments/assets/1a147c4c-68e6-4248-a429-47ef286cc9c8



中文演示：

[BiliBili](https://www.bilibili.com/video/BV1krHUeRE98/), [YouTube](https://youtu.be/cb5anPTNklw)





### 为什么选择这个项目而不是GitHub上的其他类似项目？
- 它可以在 macOS 上运行
  - 许多现有解决方案使用 VTube Studio 显示 Live2D 模型，并通过将桌面内部音频路由到 VTube Studio 并用它控制嘴唇来实现唇形同步。然而，在 macOS 上，没有简单的方法让 VTuber Studio 监听桌面上的内部音频。
  - 许多现有解决方案缺乏对 macOS 上 GPU 加速的支持，这使得它们在 Mac 上运行缓慢。
- 该项目支持 [MemGPT](https://github.com/cpacker/MemGPT) 进行永久聊天。聊天机器人会记住您说过的话。
- 如果您愿意，任何数据都不会离开您的计算机
  - 您可以选择本地 LLM/语音识别/语音合成解决方案；一切都在离线工作。在 macOS 上测试过。
- 您可以随时用您的声音打断 LLM，无需佩戴耳机。






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

### 最近的功能更新
- [2024年9月17日] 添加了 DeepLX 翻译以更改音频语言
- [2024年9月6日] 添加了 GroqWhisperASR
- [2024年9月5日] 更好的 Docker 支持
- [2024年9月1日] 添加了语音打断功能（并重构了后端）
- [2024年7月15日] 添加了 MeloTTS
- [2024年7月15日] 重构了 llm 和 launch.py 并减少了 TTS 延迟
- [2024年7月11日] 添加了 CosyVoiceTTS
- [2024年7月11日] 使用 SenseVoiceSmall 语音识别模型添加了 FunASR。
- [2024年7月7日] 使用 Nvidia GPU 直通的完全未经测试的 Docker 支持（无 Mac，无 AMD）
- [2024年7月6日] 支持中文以及其他一些语言...
- [2024年7月6日] WhisperCPP 支持 macOS GPU 加速。大大减少了 Mac 上的延迟
- ...

## 已实现的功能

- 通过语音与 LLM 对话。离线。
- ~~基于聊天历史的检索增强生成 (RAG)~~ *(暂时移除)*

当前支持的 LLM 后端
- 任何与 OpenAI API 兼容的后端，例如 Ollama、Groq、LM Studio、OpenAI 等。
- MemGPT（需要设置）

当前支持的语音识别后端
- [FunASR](https://github.com/modelscope/FunASR)，支持 [SenseVoiceSmall](https://github.com/FunAudioLLM/SenseVoice) 和许多其他模型。(~~本地~~ 目前需要互联网连接才能加载。本地计算)
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (本地)
- 使用 python 绑定 [pywhispercpp](https://github.com/abdeladim-s/pywhispercpp) 的 [Whisper-CPP](https://github.com/ggerganov/whisper.cpp)（本地，可以配置 mac GPU 加速）
- [Whisper](https://github.com/openai/whisper) (本地)
- [Groq Whisper](https://groq.com/)（需要 API 密钥）。这是一个托管的 Whisper 端点，速度很快，每天都有大量的免费限制。
- [Azure 语音识别](https://azure.microsoft.com/en-us/products/ai-services/speech-to-text) (需要 API 密钥)
- 默认情况下将使用服务器终端中的麦克风。您可以更改 `conf.yaml` 中的 `MIC_IN_BROWSER` 设置，将麦克风（和语音激活检测）移动到浏览器（目前以延迟为代价）。如果您在不同的机器或 VM 或 docker 中运行后端，您可能希望使用客户端（浏览器）上的麦克风而不是服务器上的麦克风。

当前支持的文本转语音后端
- [py3-tts](https://github.com/thevickypedia/py3-tts)（本地，它使用您系统的默认 TTS 引擎）
- [meloTTS](https://github.com/myshell-ai/MeloTTS)（本地，快速）
- [Coqui-TTS](https://github.com/idiap/coqui-ai-TTS) (本地，速度取决于您运行的模型。)
- [bark](https://github.com/suno-ai/bark) (本地，非常消耗资源)
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) (本地，非常消耗资源)
- [xTTSv2](https://github.com/daswer123/xtts-api-server) (本地，非常消耗资源)
- [Edge TTS](https://github.com/rany2/edge-tts) (在线，无需 API 密钥)
- [Azure 文本转语音](https://azure.microsoft.com/en-us/products/ai-services/text-to-speech) (在线，需要 API 密钥)

快速文本合成
- 语句到达后立即合成，因此无需等待整个 LLM 响应。
- 具有多线程的生产者-消费者模型：音频将在后台连续合成。只要新音频准备好，它们就会一个接一个地播放。音频播放器不会阻塞音频合成器。

Live2D 动画面部
- 使用 `config.yaml` 更改 Live2D 模型（模型需要在 model_dict.json 中列出）
- 加载本地 Live2D 模型。有关文档，请查看 `doc/live2d.md`。
- 使用 LLM 响应中的表情关键词来控制面部表情，因此不需要额外的模型进行情绪检测。表情关键词会自动加载到系统提示中，并从语音合成输出中排除。

live2d 技术细节
- 使用 [guansss/pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) 在*浏览器*中显示 live2d 模型
- 使用 WebSocket 控制服务器和前端之间的面部表情和说话状态
- 所有必需的包都可以在本地获得，因此前端可以离线工作。
- 您可以从 URL 或本地存储在 `live2d-models` 目录中的模型加载 live2d 模型。默认的 `shizuku-local` 存储在本地并可以离线工作。如果 model_dict.json 中模型的 URL 属性是一个 URL 而不是以 `/live2d-models` 开头的路径，则每次打开前端时都需要从指定的 URL 获取它们。阅读 `doc/live2d.md` 以获取有关从本地加载 Live2D 模型的文档。
- 运行 `server.py` 以运行 WebSocket 通信服务器，在 `./static` 文件夹中打开 `index.html` 以打开前端，并运行 ~~`launch.py`~~ `main.py` 以运行 LLM/ASR/TTS 处理的后端。

## 安装和使用

> **新的安装说明正在[这里](https://github.com/t41372/Open-LLM-VTuber/wiki)创建**

### 要求：
- ffmpeg
- Python >= 3.10, < 3.13
- 需要在 Python 3.13 上进行更多测试

克隆此存储库。

您需要准备好并运行 [Ollama](https://github.com/jmorganca/ollama) 或任何其他与 OpenAI API 兼容的后端。如果您想使用 MemGPT 作为后端，请向下滚动到 MemGPT 部分。

准备您选择的 LLM。编辑项目目录 `conf.yaml` 中的 BASE_URL 和 MODEL。


强烈建议使用 conda 或 venv 等虚拟 Python 环境！（因为依赖关系很乱！）。

在终端中运行以下命令以安装依赖项。

~~~shell
pip install -r requirements.txt # 在项目目录中运行此命令
# 根据以下说明安装语音识别依赖项和文本转语音依赖项
~~~

默认情况下，此项目启动音频交互模式，这意味着您可以通过语音与 LLM 对话，LLM 将通过语音与您交谈。

编辑 `conf.yaml` 进行配置。您可以按照演示视频中使用的配置进行操作。

如果您想使用 live2d，请运行 `server.py`。使用浏览器打开页面 `localhost:12393`（您可以更改此设置），您就准备好了。一旦 Live2D 模型出现在屏幕上，它就准备好与您交谈了。

如果您不想要 live2d，可以使用 Python 运行 `main.py` 以进入 cli 模式。

某些模型将在您首次启动时下载，这可能需要互联网连接，并且可能需要一段时间。



### 更新
如果您编辑过配置文件 `conf.yaml`，请备份它们，然后更新存储库。
或者只需再次克隆存储库并确保传输您的配置。配置文件有时会更改，因为此项目仍处于早期阶段。更新程序时要小心。




## 安装语音识别 (ASR)
编辑 `conf.yaml` 中的 ASR_MODEL 设置以更改提供商。

以下是您可以选择的语音识别选项：


`FunASR` (~~本地~~)（即使在 CPU 上也能非常快速地运行。不知道他们是怎么做到的）
- [FunASR](https://github.com/modelscope/FunASR?tab=readme-ov-file) 是来自 ModelScope 的基本端到端语音识别工具包，可以运行许多 ASR 模型。使用来自 [FunAudioLLM](https://github.com/FunAudioLLM/SenseVoice) 的 SenseVoiceSmall，结果和速度都非常好。
- 使用 `pip install -U funasr modelscope huggingface_hub` 安装。另外，确保您拥有 torch (torch>=1.13) 和 torchaudio。使用 `pip install torch torchaudio` 安装它们。
- _即使模型在本地可用_，它在启动时也需要互联网连接。请参阅 https://github.com/modelscope/FunASR/issues/1897

`Faster-Whisper` (本地)
- Whisper，但速度更快。在 macOS 上，它仅在 CPU 上运行，速度不是很快，但易于使用。
- 对于 Nvidia GPU 用户，要使用 GPU 加速，您需要安装以下 NVIDIA 库：
  -  [适用于 CUDA 12 的 cuBLAS](https://developer.nvidia.com/cublas)
  -  [适用于 CUDA 12 的 cuDNN 8](https://developer.nvidia.com/cudnn)
- 或者，如果您不需要速度，可以将 `conf.yaml` 中 `Faster-Whisper` 下的 `device` 设置为 `cpu` 以减少麻烦。


`WhisperCPP` (本地)（如果配置正确，在 Mac 上运行速度非常快）
- 如果您使用的是 Mac，请阅读以下有关设置支持 coreML 的 WhisperCPP 的说明。如果您想使用 CPU 或 Nvidia GPU，请通过运行 `pip install pywhispercpp` 来安装软件包。
- whisper cpp python 绑定。它可以通过配置在 coreML 上运行，这使得它在 macOS 上非常快。
- 在 CPU 或 Nvidia GPU 上，它可能比 Faster-Whisper 慢

WhisperCPP coreML 配置：
- 如果您已经安装了原始的 `pywhispercpp`，请卸载它。我们正在构建软件包。
- 使用 Python 运行 `install_coreml_whisper.py` 以自动为您克隆和构建支持 coreML 的 `pywhispercpp`。
- 准备合适的 coreML 模型。
  - 您可以根据 Whisper.cpp 存储库上的文档将模型转换为 coreml
  - ...或者您可以找到一些[神奇的 huggingface 存储库](https://huggingface.co/chidiwilliams/whisper.cpp-coreml/tree/main)，恰好拥有那些转换后的模型。只需记住解压缩它们即可。如果程序无法加载模型，它将产生段错误。
  - 您无需在 `conf.yaml` 中的模型名称中包含那些奇怪的前缀。例如，如果 coreML 模型的名称看起来像 `ggml-base-encoder.mlmodelc`，只需将 `base` 放入 `conf.yaml` 中 `WhisperCPP` 设置下的 `model_name` 中即可。

`Whisper` (本地)
- 来自 OpenAI 的原始 Whisper。使用 `pip install -U openai-whisper` 安装它
- 所有中最慢的。添加它作为一个实验，看看它是否可以利用 macOS GPU。它没有。

`GroqWhisperASR` (在线，需要 API 密钥)

- 来自 Groq 的 Whisper 端点。它非常快，每天都有很多免费使用量。它是预先安装的。从 [groq](https://console.groq.com/keys) 获取 API 密钥并将其添加到 `conf.yaml` 中的 GroqWhisper 设置中。
- 需要 API 密钥和互联网连接。

`AzureASR` (在线，需要 API 密钥)

- Azure 语音识别。使用 `pip install azure-cognitiveservices-speech` 安装。
- 需要 API 密钥和互联网连接。
- **⚠️ ‼️ `api_key.py` 在 `v0.2.5` 中已弃用。请在 `conf.yaml` 中设置 API 密钥。**

## 安装语音合成（文本转语音）(TTS)
安装相应的软件包并使用 `conf.yaml` 中的 `TTS_MODEL` 选项将其打开。

`pyttsx3TTS` (本地，快速)
- 使用命令 `pip install py3-tts` 安装。
- 此软件包将使用您系统上的默认 TTS 引擎。它在 Windows 上使用 `sapi5`，在 Mac 上使用 `nsss`，在其他平台上使用 `espeak`。
- 使用 `py3-tts` 而不是更著名的 `pyttsx3`，是因为 `pyttsx3` 似乎未维护，而且我无法让最新版本的 `pyttsx3` 正常工作。

`meloTTS` (本地，快速)

- 根据他们的[文档](https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md) 安装 MeloTTS（不要通过 docker 安装）（克隆存储库的一个好地方是 submodule 文件夹，但您可以将其放在任何您想要的地方）。如果您遇到与 `mecab-python` 相关的问题，请尝试此 [fork](https://github.com/polm/MeloTTS)（截至 2024 年 7 月 16 日尚未合并到主分支）。
- 它不是最好的，但绝对比 pyttsx3TTS 好，而且在我的 mac 上速度很快。如果我无法访问互联网，我会暂时选择这个（如果我可以访问互联网，我会使用 edgeTTS）。

`coquiTTS` (本地，可以快或慢，取决于您运行的模型)

- 似乎很容易安装
- 使用命令 `pip install "coqui-tts[languages]"` 安装
- 支持许多不同的 TTS 模型。使用 `tts --list_models` 命令列出所有受支持的模型。
- 默认模型是仅英语模型。
- 对中文模型使用 `tts_models/zh-CN/baker/tacotron2-DDC-GST`。（但一致性很奇怪...）
- 如果你找到了一些好的模型可以使用，请告诉我！有太多模型了，我都不知道从哪里开始...

`barkTTS` (本地，慢)

- 使用此命令 `pip install git+https://github.com/suno-ai/bark.git` 安装 pip 软件包，并在 `conf.yaml` 中将其打开。
- 首次启动时将下载所需的模型。

`cosyvoiceTTS` (本地，慢)
- 根据他们的文档配置 [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) 并启动 WebUI 演示。
- 编辑 `conf.yaml` 以匹配您所需的配置。查看他们的 WebUI 和 WebUI 上的 API 文档，以了解 `conf.yaml` 中 `cosyvoiceTTS` 设置下配置的含义。

`xTTSv2` (本地，慢)
- 建议使用 xtts-api-server，它有清晰的 api 文档，部署起来相对容易。

`edgeTTS` (在线，无需 API 密钥)
- 使用此命令 `pip install edge-tts` 安装 pip 软件包，并在 `conf.yaml` 中将其打开。
- 听起来很不错。运行速度很快。
- 使用 edge tts 时，请记住连接到互联网。

`AzureTTS` (在线，需要 API 密钥) (这与 neuro-sama 使用的 TTS 完全相同)

- 使用命令 `pip install azure-cognitiveservices-speech` 安装 Azure SDK。
- 从 Azure 获取 API 密钥（用于文本转语音）。
- **⚠️ ‼️ `api_key.py` 在 `v0.2.5` 中已弃用。请在 `conf.yaml` 中设置 API 密钥。**
- `conf.yaml` 中的默认设置是 neuro-sama 使用的语音。



如果您使用的是 macOS，则需要启用终端模拟器的麦克风权限（您是在终端中运行此程序的，对吧？为您的终端启用麦克风权限）。如果您未能这样做，语音识别将无法听到您的声音，因为它没有使用麦克风的权限。



## 翻译

实现了 DeepLX 翻译，让程序可以用与对话语言不同的语言说话。例如，LLM 可能用英语思考，字幕是英语，您说的是英语，但 LLM 的语音是日语。这是通过在发送句子进行音频生成之前对其进行翻译来实现的。

目前 DeepLX 是唯一支持的翻译后端。其他提供商将很快实施。

### 启用音频翻译

1. 将 `conf.yaml` 中的 `TRANSLATE_AUDIO` 设置为 True
2. 将 `DEEPLX_TARGET_LANG` 设置为您想要的语言。确保此语言与 TTS 说话者的语言匹配（例如，如果 `DEEPLX_TARGET_LANG` 是“JA”，即日语，则 TTS 也应说日语。）。





## MemGPT （可能已损坏）

> :warning: MemGPT 已重命名为 Letta，并更改了许多与其 API 及其功能相关的内容。截至目前，此项目中 MemGPT 的集成尚未使用最新更改进行更新。

> MemGPT 集成非常实验性，需要大量设置。此外，MemGPT 需要一个强大的 LLM（大于 7b 且量化高于 Q5），具有大量的标记占用空间，这意味着它要慢得多。
> 不过，MemGPT 确实有自己的免费 LLM 端点。您可以用它来测试。查看他们的文档。

此项目可以使用 [MemGPT](https://github.com/cpacker/MemGPT) 作为其 LLM 后端。MemGPT 使 LLM 具有长期记忆。

要使用 MemGPT，您需要配置并运行 MemGPT 服务器。您可以使用 `pip` 或 `docker` 安装它，或者在不同的机器上运行它。查看他们的 [GitHub 存储库](https://github.com/cpacker/MemGPT) 和[官方文档](https://memgpt.readme.io/docs/index)。

> :warning:
> 我建议您在单独的 Python 虚拟环境或 docker 中安装 MemGPT，因为此项目和 MemGPT 之间目前存在依赖项冲突（在快速 API 上，似乎是这样）。您可以查看此问题 [您能否升级依赖项中的 typer 版本 #1382](https://github.com/cpacker/MemGPT/issues/1382)。



以下是一个清单：
- 安装 memgpt
- 配置 memgpt
- 使用 `memgpt server` 命令运行 `memgpt`。记住在启动 Open-LLM-VTuber 之前让服务器运行。
- 通过其 cli 或 web UI 设置一个代理。将您的系统提示以及 Live2D 表达式提示和您要使用的表达式关键字（在 `model_dict.json` 中找到它们）添加到 MemGPT 中
- 将 `server admin password` 和 `Agent id` 复制到 `./llm/memgpt_config.yaml` 中。*顺便说一句，`agent id` 不是代理的名称*。
- 在 `conf.yaml` 中将 `LLM_PROVIDER` 设置为 `memgpt`。
- 请记住，如果您使用 `memgpt`，`conf.yaml` 中所有与 LLM 相关的配置都将被忽略，因为 `memgpt` 不是那样工作的。



## Mem0（开发中）

另一个长期记忆解决方案。仍在开发中。高度实验性。

优点

- 与 MemGPT 相比，它更容易设置
- 它比 MemGPT 快一点（但仍然需要更多的 LLM 标记来处理）

缺点

- 它只记住你的偏好和想法，其他什么都不记得。它不记得 LLM 说过什么。
- 它并不总是把东西放入内存。
- 它有时会记住错误的东西
- 它需要一个具有非常好的函数调用能力的 LLM，这对于较小的模型来说是相当困难的
- 



# 问题

缺少 `PortAudio`
- 通过您的包管理器（如 apt）将 `libportaudio2` 安装到您的计算机上



# 在容器中运行 [高度实验性]

:warning: 这是高度实验性的，但我认为它有效。大多数时候。

您可以自己构建镜像，也可以从 docker hub 中提取它。[![](https://img.shields.io/badge/t41372%2FOpen--LLM--VTuber-%25230db7ed.svg?logo=docker&logoColor=blue&labelColor=white&color=blue)](https://hub.docker.com/r/t41372/open-llm-vtuber)

- （但镜像大小非常大）
- docker hub 上的镜像可能不会像它那样定期更新。GitHub action 无法构建如此大的镜像。我可能会研究其他选项。



当前问题：

- 镜像大小很大（~20GB），并且需要更多空间，因为某些模型是可选的，并且仅在使用时才会下载。
- 需要 Nvidia GPU（GPU 直通限制）
- 需要配置 [Nvidia 容器工具包](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) 以进行 GPU 直通。
- 如果您停止容器，则必须再次下载某些模型。（将修复）
- 不要在 Arm 机器上构建镜像。由于某种原因，其中一个依赖项（准确地说是 grpc）将失败 https://github.com/grpc/grpc/issues/34998。
- 正如前面提到的，除非网页有 https，否则您无法在远程服务器上运行它。这是因为前端的网络麦克风将仅在安全上下文中启动（这意味着仅限本地主机或 https 环境）。

大多数 asr 和 tts 将预先安装。但是，bark TTS 和原始 OpenAI Whisper（`Whisper`，而不是 WhisperCPP）不包含在默认构建过程中，因为它们很大（~8GB，这使得整个容器大约 25GB）。此外，它们也没有提供最佳性能。要在镜像中包含 bark 和/或 whisper，请将参数 `--build-arg INSTALL_ORIGINAL_WHISPER=true --build-arg INSTALL_BARK=true` 添加到镜像构建命令中。

设置指南：

1. 在构建之前查看 `conf.yaml`（当前已刻录到镜像中，很抱歉）：

2. 构建镜像：

 ```
 docker build -t open-llm-vtuber .
 ```

 （去喝杯饮料，这需要一段时间）

3. 获取 `conf.yaml` 配置文件。
 从此存储库获取 `conf.yaml` 文件。或者您可以直接从此 [链接](https://raw.githubusercontent.com/t41372/Open-LLM-VTuber/main/conf.yaml) 获取它。

4. 运行容器：

`$(pwd)/conf.yaml` 应该是您的 `conf.yaml` 文件的路径。

 ```
 docker run -it --net=host --rm -v $(pwd)/conf.yaml:/app/conf.yaml -p 12393:12393 open-llm-vtuber
 ```

5. 打开 localhost:12393 进行测试

# 开发
（这个项目处于积极的原型设计阶段，所以很多东西都会改变）

本项目中使用的一些缩写：

- LLM：大型语言模型
- TTS：文本转语音、语音合成、语音合成
- ASR：自动语音识别、语音识别、语音转文本、STT
- VAD：语音激活检测

### 关于采样率

您可以假设整个项目中的采样率为 `16000`。
前端将采样率为 `16000` 的 `Float32Array` 块流式传输到后端。

### 添加对新 TTS 提供商的支持
1. 实现 `tts/tts_interface.py` 中定义的 `TTSInterface`。
1. 将您的新 TTS 提供商添加到 `tts_factory` 中：用于实例化和返回 tts 实例的工厂。
1. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递到您的 TTSEngine 的构造函数中。

### 添加对新语音识别提供商的支持
1. 实现 `asr/asr_interface.py` 中定义的 `ASRInterface`。
2. 将您的新 ASR 提供商添加到 `asr_factory` 中：用于实例化和返回 ASR 实例的工厂。
3. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递到您的类的构造函数中。

### 添加对新 LLM 提供商的支持
1. 实现 `llm/llm_interface.py` 中定义的 `LLMInterface`。
2. 将您的新 LLM 提供商添加到 `llm_factory` 中：用于实例化和返回 LLM 实例的工厂。
3. 将配置添加到 `conf.yaml`。具有相同名称的字典将作为 kwargs 传递到您的类的构造函数中。

# 致谢
我从中学习的优秀项目

- https://github.com/dnhkng/GlaDOS
- https://github.com/SchwabischesBauernbrot/unsuperior-ai-waifu
- https://codepen.io/guansss/pen/oNzoNoz
- https://github.com/Ikaros-521/AI-Vtuber
- https://github.com/zixiiu/Digital_Life_Server



## Star 历史记录

[![Star 历史记录图表](https://api.star-history.com/svg?repos=t41372/open-llm-vtuber&type=Date)](https://star-history.com/#t41372/open-llm-vtuber&Date)


