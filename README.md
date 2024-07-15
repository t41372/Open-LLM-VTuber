# Open-LLM-VTuber

> :warning: This project is in its early stages and is currently under **active development**. Features are unstable, code is messy, and breaking changes will occur. The main goal of this stage is to build a minimum viable prototype using technologies that are easy to integrate.

> :warning: If you want to run this program on a server and access it remotely on your laptop, the microphone on the front end will only launch in a secure context (a.k.a. https or localhost). See [MDN Web Doc](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia). Therefore, you might want to either configure https with a reverse proxy or launch the front end locally and connects to the server via websocket (untested). Open the `static/index.html` with your browser and set the ws url on the page.

Open-LLM-VTuber allows you to talk to any LLM by voice locally with a Live2D talking face. The LLM inference backend, speech recognition, and speech synthesizer are all designed to be swappable. This project can be configured to run offline on macOS, Linux, and Windows. 

Long-term memory with MemGPT can be configured to achieve perpetual chat, infinite* context length, and external data source.

This project started as an attempt to recreate the closed-source AI VTuber `neuro-sama` with open-source alternatives that can run offline on platforms other than Windows.


<img width="500" alt="demo-image" src="https://github.com/t41372/Open-LLM-VTuber/assets/36402030/fa363492-7c01-47d8-915f-f12a3a95942c"/>





https://github.com/t41372/Open-LLM-VTuber/assets/36402030/e8931736-fb0b-4cab-a63a-eea5694cbb83
- The demo video uses llama3 (Q4_0) with Ollama, edgeTTS, and WhisperCPP running the coreML version of the small model.





### Why this project and not other similar projects on GitHub?
- It works on macOS
  - Many existing solutions display Live2D models using VTube Studio and achieve lip sync by routing desktop internal audio into VTube Studio and controlling the lips with that. On macOS, however, there is no easy way to let VTuber Studio listen to internal audio on the desktop.
- It supports [MemGPT](https://github.com/cpacker/MemGPT) for perpetual chat. The chatbot remembers what you've said.
- No data leaves your computer if you wish to
  - You can choose local LLM/voice recognition/speech synthesis solutions, and everything will work offline. Everything has been tested on macOS.






### Basic Goals
- [x] Chat with LLM by voice
- [x] Choose your own LLM backend
- [x] Choose your own Speech Recognition & Text to Speech provider
- [x] Long-term memory
- [x] Live2D frontend

### Target Platform
- macOS
- Windows
- Linux

### Recent Feature Updates
- [Jul 15, 2024] Refactored llm and launch.py and reduced TTS latency
- [Jul 11, 2024] Added CosyVoiceTTS
- [Jul 11, 2024] Added FunASR with SenseVoiceSmall speech recognition model.
- [Jul 7, 2024] Totally untested Docker support with Nvidia GPU passthrough (no Mac, no AMD)
- [Jul 6, 2024] Support for Chinese 支持中文 and probably some other languages...
- [Jul 6, 2024] WhisperCPP with macOS GPU acceleration. Dramatically decreased latency on Mac
- ...

## Implemented Features

- Talk to LLM with voice. Offline.
- ~~RAG on chat history~~ *(temporarily removed)*

Currently supported LLM backend
- Any OpenAI-API-compatible backend, such as Ollama, Groq, LM Studio, OpenAI, and more.
- MemGPT (setup required)

Currently supported Speech recognition backend
- [FunASR](https://github.com/modelscope/FunASR), which support [SenseVoiceSmall](https://github.com/FunAudioLLM/SenseVoice) and many other models. (~~Local~~ Currently requires an internet connection for loading. Compute locally)
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (Local)
- [Whisper-CPP](https://github.com/ggerganov/whisper.cpp) using the python binding [pywhispercpp](https://github.com/abdeladim-s/pywhispercpp) (Local, mac GPU acceleration can be configured)
- [Whisper](https://github.com/openai/whisper) (local)
- [Azure Speech Recognition](https://azure.microsoft.com/en-us/products/ai-services/speech-to-text) (API Key required)
- The microphone in the server terminal will be used by default. You can change the setting `MIC_IN_BROWSER` in the `conf.yaml` to move the microphone (and voice activation detection) to the browser (at the cost of latency, for now). You might want to use the microphone on your client (the browser) rather than the one on your server if you run the backend on a different machine or inside a VM or docker.

Currently supported Text to Speech backend
- [py3-tts](https://github.com/thevickypedia/py3-tts) (Local, it uses your system's default TTS engine)
- [bark](https://github.com/suno-ai/bark) (Local, very resource-consuming)
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) (Local, very resource-consuming)
- [Edge TTS](https://github.com/rany2/edge-tts) (online, no API key required)
- [Azure Text-to-Speech](https://azure.microsoft.com/en-us/products/ai-services/text-to-speech) (online, API Key required)

Fast Text Synthesis
- Synthesize sentences as soon as they arrive, so there is no need to wait for the entire LLM response.
- Producer-consumer model with asyncio: Audio will be continuously synthesized in the background. They will be played one by one whenever the new audio is ready. The audio player will not block the audio synthesizer.

Live2D Talking face
- Change Live2D model with `config.yaml` (model needs to be listed in model_dict.json)
- Load local Live2D models. Check `doc/live2d.md` for documentation.
- Uses expression keywords in LLM response to control facial expression, so there is no additional model for emotion detection. The expression keywords are automatically loaded into the system prompt and excluded from the speech synthesis output.

live2d technical details
- Uses [guansss/pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) to display live2d models in *browser*
- Uses WebSocket to control facial expressions and talking state between the server and the front end
- All the required packages are locally available, so the front end works offline. 
- You can load live2d models from a URL or the one stored locally in the `live2d-models` directory. The default `shizuku-local` is stored locally and works offline. If the URL property of the model in the model_dict.json is a URL rather than a path starting with `/live2d-models`, they will need to be fetched from the specified URL whenever the front end is opened. Read `doc/live2d.md` for documentation on loading your live2D model from local.
- Run the `server.py` to run the WebSocket communication server, open the `index.html` in the `./static` folder to open the front end, and run `launch.py` to run the backend for LLM/ASR/TTS processing.

## Install & Usage

Install FFmpeg on your computer.

Clone this repository.

You need to have [Ollama](https://github.com/jmorganca/ollama) or any other OpenAI-API-Compatible backend ready and running. If you want to use MemGPT as your backend, scroll down to the MemGPT section.

Prepare the LLM of your choice. Edit the BASE_URL and MODEL in the project directory's `conf.yaml`.


This project was developed using Python `3.10.13`. I strongly recommend creating a virtual Python environment like conda for this project. 

Run the following in the terminal to install the dependencies.

~~~shell
pip install -r requirements.txt # Run this in the project directory
# Install Speech recognition dependencies and text-to-speech dependencies according to the instructions below
~~~

This project, by default, launches the audio interaction mode, meaning you can talk to the LLM by voice, and the LLM will talk back to you by voice.

Edit the `conf.yaml` for configurations. You can follow the configuration used in the demo video.

If you want to use live2d, run `server.py` to launch the WebSocket communication server and open the URL you set in `conf.yaml` (`http://HOST:PORT`). By default, go to `http://localhost:8000`.

Run `launch.py` with Python. Some models will be downloaded during your first launch, which may take a while.

Also, the live2D models have to be fetched through the internet, so you'll have to keep your internet connected before the `index.html` is fully loaded with your desired live2D model.



### Update
Back up the configuration files `conf.yaml` if you've edited them, and then update the repo.
Or just clone the repo again and make sure to transfer your configurations. The configuration file will sometimes change because this project is still in its early stages. Be cautious when updating the program.




## Install Speech Recognition
Edit the ASR_MODEL settings in the `conf.yaml` to change the provider.

Here are the options you have for speech recognition:


`FunASR` (~~local~~) (Runs very fast even on CPU. Not sure how they did it)
- [FunASR](https://github.com/modelscope/FunASR?tab=readme-ov-file) is a Fundamental End-to-End Speech Recognition Toolkit from ModelScope that runs many ASR models. The result and speed are pretty good with the SenseVoiceSmall from [FunAudioLLM](https://github.com/FunAudioLLM/SenseVoice) at Alibaba Group.
- Install with `pip install -U funasr modelscope huggingface_hub`
- It requires an internet connection on launch _even if the models are locally available_. See https://github.com/modelscope/FunASR/issues/1897

`Faster-Whisper` (local)
- Whisper, but faster. On macOS, it runs on CPU only, which is not so fast, but it's easy to use.

`WhisperCPP` (local) (runs super fast on a Mac if configured correctly)
- If you are on a Mac, read below for instructions on setting up WhisperCPP with coreML support. If you want to use CPU or Nvidia GPU, install the package by running `pip install pywhispercpp`.
- The whisper cpp python binding. It can run on coreML with configuration, which makes it very fast on macOS.
- On CPU or Nvidia GPU, it's probably slower than Faster-Whisper

WhisperCPP coreML configuration:
- Uninstall the original `pywhispercpp` if you have already installed it. We are building the package.
- Run `install_coreml_whisper.py` with Python to automatically clone and build the coreML-supported `pywhispercpp` for you.
- Prepare the appropriate coreML models.
  - You can either convert models to coreml according to the documentation on Whisper.cpp repo
  - ...or you can find some [magical huggingface repo](https://huggingface.co/chidiwilliams/whisper.cpp-coreml/tree/main) that happens to have those converted models. Just remember to decompress them. If the program fails to load the model, it will produce a segmentation fault.
  - You don't need to include those weird prefixes in the model name in the `conf.yaml`. For example, if the coreml model's name looks like `ggml-base-encoder.mlmodelc`, just put `base` into the `model_name` under `WhisperCPP` settings in the `conf.yaml`.

`Whisper` (local)
- Original Whisper from OpenAI. Install it with `pip install -U openai-whisper`
- The slowest of all. Added as an experiment to see if it can utilize macOS GPU. It didn't.

`AzureASR` (online, API Key required)
- Azure Speech Recognition. Install with `pip install azure-cognitiveservices-speech`.
- API key and internet connection are required.

## Install Speech Synthesis (text to speech)
Install the respective package and turn it on using the `TTS_MODEL` option in `conf.yaml`.

`pyttsx3TTS` (local, fast)
- Install with the command `pip install py3-tts`.
- This package will use the default TTS engine on your system. It uses `sapi5` on Windows, `nsss` on Mac, and `espeak` on other platforms.
- `py3-tts` is used instead of the more famous `pyttsx3` because `pyttsx3` seems unmaintained, and I couldn't get the latest version of `pyttsx3` working.



`barkTTS` (local, slow)
- Install the pip package with this command `pip install git+https://github.com/suno-ai/bark.git` and turn it on in `conf.yaml`.
- The required models will be downloaded on the first launch.

`cosyvoiceTTS` (local, slow)
- Configure [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) and launch the webui demo according to their documentation. 
- Edit `conf.yaml` to match your desired configurations. Check their webui and the API documentation on the webui to see the meaning of the configurations under the setting `cosyvoiceTTS` in the `conf.yaml`.

`edgeTTS` (online, no API key required)
- Install the pip package with this command `pip install edge-tts` and turn it on in `conf.yaml`.
- It sounds pretty good. Runs pretty fast.
- Remember to connect to the internet when using edge tts.

`AzureTTS` (online, API key required)
- See below

### Azure API for Speech Recognition and Speech to Text, API key needed

Create a file named `api_keys.py` in the project directory, paste the following text into the file, and fill in the API keys and region you gathered from your Azure account.

~~~python
# Azure API key
AZURE_API_Key="YOUR-API-KEY-GOES-HERE"

# Azure region
AZURE_REGION="YOUR-REGION"

# Choose the Text to speech model you want to use
AZURE_VOICE="en-US-AshleyNeural"
~~~



If you're using macOS, you need to enable the microphone permission of your terminal emulator (you run this program inside your terminal, right? Enable the microphone permission for your terminal). If you fail to do so, the speech recognition will not be able to hear you because it does not have permission to use your microphone.


## MemGPT
> MemGPT integration is very experimental and requires quite a lot of setup. In addition, MemGPT requires a powerful LLM (larger than 7b and quantization above Q5) with a lot of token footprint, which means it's a lot slower.
> MemGPT does have its own LLM endpoint for free, though. You can test things with it. Check their docs.

This project can use [MemGPT](https://github.com/cpacker/MemGPT) as its LLM backend. MemGPT enables LLM with long-term memory.

To use MemGPT, you need to have the MemGPT server configured and running. You can install it using `pip` or `docker` or run it on a different machine. Check their [GitHub repo](https://github.com/cpacker/MemGPT) and [official documentation](https://memgpt.readme.io/docs/index).

> :warning:
> I recommend you install MemGPT either in a separate Python virtual environment or in docker because there is currently a dependency conflict between this project and MemGPT (on fast API, it seems). You can check this issue [Can you please upgrade typer version in your dependancies #1382](https://github.com/cpacker/MemGPT/issues/1382).



Here is a checklist:
- Install memgpt
- Configure memgpt
- Run `memgpt` using `memgpt server` command. Remember to have the server running before launching Open-LLM-VTuber.
- Set up an agent either through its cli or web UI. Add your system prompt with the Live2D Expression Prompt and the expression keywords you want to use (find them in `model_dict.json`) into MemGPT
- Copy the `server admin password` and the `Agent id` into `./llm/memgpt_config.yaml`
- Set the `LLM_PROVIDER` to `memgpt` in `conf.yaml`. 
- Remember, if you use `memgpt`, all LLM-related configurations in `conf.yaml` will be ignored because `memgpt` doesn't work that way.



# Issues

`PortAudio` Missing
- Install `libportaudio2` to your computer via your package manager like apt



# Running in a Container

:warning: This is highly experimental, totally untested (because I use a mac), and totally unfinished. If you are having trouble with all the dependencies, however, you can try to have trouble with the container instead, which is still a lot of trouble but is a different set of trouble, I guess.

Current issues:

- Large image size (7-13GB)
- Nvidia GPU required (GPU passthrough limitation)
- [Nvidia Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) needs to be configured for GPU passthrough.
- You can't run it on a remote server unless you have configured SSL for the front end (it's not a feature of this project quite yet, so you may do a reverse proxy). That's because the web mic on the front end will only launch in a secure context (which refers to localhost or https environment). 
- I'm not sure if it works (because I use mac and the added complexity caused by the reason mentioned above)
- Don't build the image on an Arm machine. One of the dependencies (grpc, to be exact) will fail for some reason https://github.com/grpc/grpc/issues/34998. 

Setup guide:

1. Review `conf.yaml` before building (currently burned into the image, I'm sorry):

   - Set `MIC_IN_BROWSER` to true (required because your mic doesn't live inside the container)

2. Build the image:

 ```
 docker build -t open-llm-vtuber .
 ```

 (Grab a drink, this may take a while)

3. Run the container:

 ```
 docker run -it --net=host -p 8000:8000 open-llm-vtuber "sh"
 ```

4. Inside the container, run:

   - `server.py`
   - Open the frontend website in your browser
   - `launch.py`
 (Use screen, tmux, or similar to run server.py and launch.py simultaneously)

5. Open localhost:8000 to test

# Development
(this project is in the active prototyping stage, so many things will change)

Some abbreviations used in this project:

- LLM: Large Language Model
- TTS: Text-to-speech, Speech Synthesis, Voice Synthesis
- ASR: Automatic Speech Recognition, Speech recognition, Speech to text, STT
- VAD: Voice Activation Detection

### Add support for new TTS providers
1. Implement `TTSInterface` defined in `tts/tts_interface.py`.
1. Add your new TTS provider into `tts_factory`: the factory to instantiate and return the tts instance.
1. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your TTSEngine as kwargs.

### Add support for new Speech Recognition provider
1. Implement `ASRInterface` defined in `asr/asr_interface.py`.
2. Add your new ASR provider into `asr_factory`: the factory to instantiate and return the ASR instance.
3. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your class as kwargs.

### Add support for new LLM provider
1. Implement `LLMInterface` defined in `llm/llm_interface.py`.
2. Add your new LLM provider into `llm_factory`: the factory to instantiate and return the LLM instance.
3. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your class as kwargs.

# Acknowledgement
Awesome projects I learned from

- https://github.com/dnhkng/GlaDOS
- https://github.com/SchwabischesBauernbrot/unsuperior-ai-waifu
- https://codepen.io/guansss/pen/oNzoNoz
- https://github.com/Ikaros-521/AI-Vtuber
- https://github.com/zixiiu/Digital_Life_Server





