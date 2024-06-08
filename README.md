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



### Current Features

- Talk to LLM with voice
- RAG on chat history

Currently supported LLM backend
- Ollama (for now)

Currently supported Speech recognition backend
- Faster-Whisper
- Azure Speech Recognition (API required)

Currently supported Text to Speech backend
- Azure Text-to-Speech

No live2D yet. I am still trying to figure out how to make live2D work on Mac.



### Install

Clone this repository.

You need to have [Ollama](https://github.com/jmorganca/ollama) running on a server or your local computer.

Download the LLM of your choice. Edit the BASE_URL and MODEL in the project directory's `conf.yaml`.


This project was developed using Python 3.10.13. I recommend creating a virtual Python environment like conda for this project. 

Run the following in the terminal to install the dependencies.

~~~shell
pip install -r requirements.txt # run this in the project directory
pip install azure-cognitiveservices-speech # install azure dependencies for speech recognition and text to speech.
~~~

This project, by default, launches the audio interaction mode, meaning you can talk to the LLM by voice, and the LLM will talk back to you by voice as well. You need to set up your Azure API key.

### Change Speech Recognition and Text to Speech provider
Edit the STT_MODEL and TTS MODEL settings in the `conf.yaml` to change the provider.


### Azure API for Speech Recognition and Speech to Text

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

