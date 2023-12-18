## Open-LLM-VTuber

> :warning: This project is in the **prototyping stage**. Most of the features and promises have not yet been implemented. The main goal of this stage is to build a minimum viable prototype using technologies that are easy to integrate.

This project is an attempt to recreate the closed-source AI VTuber `neuro-sama` with open-source alternatives that **run completely offline on both macOS and Windows**. You don't want your chat history with your *digital pet* to be seen by OpenAI researchers right? And... you don't want your *digital pet* to care about something as *trivial* and *insignificant* as morality right?

Written in Python ~~with Langchain~~. Using Ollama as the LLM server. Support **macOS** (first-class citizen 🙌because I'm using Mac) and **Windows** **(not yet)**


https://github.com/t41372/LangChain-Lab-04-Ollama/assets/36402030/81d68b96-e3d8-4bd1-a46e-c3a3e823486e


### Words from an incompetent developer

This is my first Python and actual serious LLM project, and I have never dealt with Live2D things before. I still have a lot to learn. If you have a better understanding and want to make this project better, feel free to open a pull request.

> BTW, I don't like Langchain. I think it's a bit overcomplicated. I use it because I still have very limited knowledge about LLM, especially vector database and memory, and I want to be able to integrate more things in the future. Maybe it's because I'm a newbie, but that doesn't change my negative opinions about Langchain. I feel like I have spent more effort and enjoyed more frustration in getting Langchain to work properly than learning Python as a whole. Langchain is poorly documented with a steep learning curve in my opinion, and is causing more problem by itself than in my opinion, dealing with those tools directly. 

*UPDATE*: Langchain has been completely removed! The project now manages the communication with the Ollama server directly. It's way easier. Ollama has memory and system prompting built-in, so the performance is awesome compare to the performance I was getting when using Langchain.

### Tech Stack & Current Project State

Current Project State:

What's working:

- We can talk to the LLM by voice and hear the LLM directly with Azure API in the terminal now.
- LLM short-term memory is implemented. The LLM can now remember what you've said.

What's NOT working:

LLM:

- Long-term memory is not implemented.
- You cannot load *base models*, you can only load instruction fine-tuned models. Technically you can load base models, but the LLM will not answer you properly.

Live2D

- No live2D yet. 



I want this project to be as modular as possible, so I tried modularizing most of the functionalities into different Python files, in the hope that one day I can swap them like swapping eggs.

Ollama Server (running as a separate server taking HTTP API calls from `Ollama.py`)

- You can install and load any open-source LLM models into Ollama. I'm using `mistral 7B instruction`, tagged `mistral:latest` in Ollama package manager.

Ollama Class (`Ollama.py`)

- handling the communication with the Ollama Server

Speech to Text, Speech Recognition (`speech2text.py`)

- Azure Speech to Text service for now. Performing real-time speech recognition and throwing the results into the LLM
- I'm looking for ways to integrate real-time speech recognition with `Whisper 3` from Open AI, but struggling to run it on my Mac or non-cuda environment. `whisper.cpp` can do that, but I don't know how to integrate it into Python with real-time speech recognition. I'm thinking about [whispercpp PyBind](https://github.com/aarnphm/whispercpp), but it is not well documented. I don't know how to integrate that with real-time speech recognition.

Text to Speech, TTS (`text2speech.py`)

- Azure for now as well. 
- I want to use Vits, but I have very little knowledge about this thing. It seems like I will have to train a voice model to use it, so I will leave it to the future.

Live2D puppet

- No Live2D yet. I'm thinking about VTube Studio, but I am not very familiar with this thing. Some similar project used Unreal Engine 5, but I don't really know how that works, and I'm worried about its macOS compatibility. Overall, I don't know how to do this.



### Install

Clone this repository.

Rename the `default.env` to `.env`, and/or adjust parameters as you wish.

You need to have [Ollama](https://github.com/jmorganca/ollama) running either on a server or on your local computer. 

Ollama has a package-manager-like tool to install and run open-source LLM with one command (like docker). Similar to docker, you don't actually need to pull the LLM before running. The model will be automatically downloaded when running the program. To be safe, you can run `ollama run mistral:latest` or `ollama pull mistral:latest` to download the model. If you want to change the LLM model, change the `.env` file in the project.



This project is developed in `Python 3.10.13`. If anything goes wrong, try checking if your Python version matches mine. I recommend using `conda` to create a virtual Python environment for this project. 

Run the following in the terminal to install the dependencies

~~~shell
pip install -r requirements.txt # run this in the project directory
pip install azure-cognitiveservices-speech # install azure dependencies for speech recognition and text to speech.
~~~

This project, by default, launches the audio interaction mode, meaning you can talk to the LLM by voice and the LLM will talk back to you back voice as well. You need to set up your Azure API key



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



If you're using macOS, you need to enable the microphone permission of your terminal emulator (you run this program inside your terminal right? Enable the microphone permission of your terminal). If you fail to do so, the speech recognition will not be able to hear you because it does have permission to use your microphone.







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

