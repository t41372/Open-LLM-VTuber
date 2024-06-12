## Open-LLM-VTuber

> :warning: This project is in the **prototyping stage**. Most of the features and promises still need to be implemented. The main goal of this stage is to build a minimum viable prototype using technologies that are easy to integrate.

This project started as an attempt to recreate the closed-source AI VTuber `neuro-sama` with open-source alternatives that **run completely offline on macOS and Windows**.

https://github.com/t41372/LangChain-Lab-04-Ollama/assets/36402030/81d68b96-e3d8-4bd1-a46e-c3a3e823486e

### Goal
- Chat with LLM by voice
- Choose your own LLM backend
- Choose your own Speech Recognition & Text to Speech provider
- Long-term memory
- Add live2D frontend

### Target Platform
- macOS
- Windows
- Linux



### Implemented Features

- Talk to LLM with voice, completely offline
- RAG on chat history

Currently supported LLM backend
- Ollama (for now)

Currently supported Speech recognition backend
- Faster-Whisper (Local)
- Azure Speech Recognition (API required)

Currently supported Text to Speech backend
- py3-tts (Local, it uses your system default tts engine)
- Azure Text-to-Speech (API required)

The Live2D feature is currently under active development.
- uses [guansss/pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) to display live2d models in browser
- uses WebSocket to control facial expressions and talking state between the server and the front end
- The live2d implementation in this project is currently in its early stages (and I'm not the most experienced front-end dev in this world). The front end currently requires an internet connection to load the live2d models and the required front-end packages, so it's not completely offline yet. Once the page is loaded, you can disconnect the internet.
- Run the `server.js` to run the WebSocket communication server, open the `index.html` in the `./static` folder to open the front end, and run `launch.py` to run the backend for LLM/ASR/TTS processing.

### Install

Clone this repository.

You need to have [Ollama](https://github.com/jmorganca/ollama) running on a server or your local computer.

Download the LLM of your choice. Edit the BASE_URL and MODEL in the project directory's `conf.yaml`.


This project was developed using Python 3.10.13. I recommend creating a virtual Python environment like conda for this project. 

Run the following in the terminal to install the dependencies.

~~~shell
pip install -r requirements.txt # run this in the project directory
pip install azure-cognitiveservices-speech # If you want to use Azure for Speech Recognition or Text to Speech, install azure dependencies.
pip install py3-tts # if you want to use py3-tts as your text to speech backend, install py3-tts
~~~

This project, by default, launches the audio interaction mode, meaning you can talk to the LLM by voice, and the LLM will talk back to you by voice as well. You need to set up your Azure API key.

### Change Speech Recognition and Text to Speech provider
Edit the STT_MODEL and TTS MODEL settings in the `conf.yaml` to change the provider.

### Use your system Text-to-Speech Engine, offline
Run the following command to install `py3-tts` package.
~~~sh
pip install py3-tts
~~~
`py3-tts` is used instead of the more famous `pyttsx3` because I couldn't get the latest version of the latter working.
In addition, `pyttsx3` is unmaintained.

This library will use the appropriate TTS engine on your machine. It uses `sapi5` on Windows, `nsss` on mac, and `espeak` on other platforms.

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





# Development
(this project is in the active prototyping stage, so many things will change)

### How to add support for new TTS provider
1. Create the new class `TTSEngine` in a new py file in the `./tts` directory
2. In the class, expose a speak function: `speak(self, text, on_speak_start_callback=None, on_speak_end_callback=None)` that runs the tts synchronously.
3. Add your new tts module into the `tts_module_name` dictionary, which is currently hard-coded in the `main.py` and `launch.py` (I plan to ditch the main.py in the future). The dictionary key is the name of the TTS provider. The value is the module path of your module.
4. Now you should be able to switch to the tts provider of your choice by editing the `conf.yaml`
5. Create a pull request

### How to add support for new Speech Recognition (or speech-to-text, STT) provider
1. Create the new class `VoiceRecognition` in a new py file in the `./speech2text` directory
2. In the class, expose a function: `transcribe_once(self)` that starts the voice recognition service. This function should be able to keep listening in the background, and when the user speaks something and finishes, the function should return the recognized text.
3. Add your new stt module into the `stt_module_name` dictionary, which is currently hard-coded in the `main.py` and `launch.py` (I plan to ditch the main.py in the future). The key of the dictionary is the name of the speech recognition provider. The value is the module path of your module.
4. Now you should be able to switch to the stt provider of your choice by editing the `conf.yaml`
5. Create a pull request






---







## Disregard the following



如果要使用 Azure TTS 作为文字转语音的引擎，需要在 `.env` 文件中选中 AzureTTS, 并添加api keys
pip install azure-cognitiveservices-speech








### 语音识别
在macOS上运行，记得要把运行本程序的终端机的麦克风权限打开，否则程序会听不到声音


### Whisper Local Speech to Text

[aarnphm/whispercpp](https://github.com/aarnphm/whispercpp)
~~~python
pip install git+https://github.com/aarnphm/whispercpp.git -vv
~~~

