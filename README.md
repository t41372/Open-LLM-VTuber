![](./banner.jpg)

<h1 align="center">Open-LLM-VTuber</h1>
<h3 align="center">

[中文](https://github.com/t41372/Open-LLM-VTuber/blob/main/README.CN.md)

[![GitHub release](https://img.shields.io/github/v/release/t41372/Open-LLM-VTuber)](https://github.com/t41372/Open-LLM-VTuber/releases) 
[![license](https://img.shields.io/github/license/t41372/Open-LLM-VTuber)](https://github.com/t41372/Open-LLM-VTuber/blob/master/LICENSE) 
[![FOSSA Status](https://fossa.app/api/projects/custom%2B50595%2Fgithub.com%2Ft41372%2FOpen-LLM-VTuber.svg?type=shield&issueType=security)](https://fossa.app/projects/custom%2B50595%2Fgithub.com%2Ft41372%2FOpen-LLM-VTuber?ref=badge_shield&issueType=security)
[![](https://img.shields.io/badge/t41372%2FOpen--LLM--VTuber-%25230db7ed.svg?logo=docker&logoColor=blue&labelColor=white&color=blue)](https://hub.docker.com/r/t41372/open-llm-vtuber) 
[![](https://img.shields.io/badge/todo_list-GitHub_Project-blue)](https://github.com/users/t41372/projects/1/views/1)


[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/yi.ting)
[![](https://dcbadge.limes.pink/api/server/3UDA8YFDXx)](https://discord.gg/3UDA8YFDXx)

</h3>

(QQ群: 792615362）<- way more active than Discord group with over 900 population and majority of the contributors
> 常见问题 Common Issues doc (Written in Chinese): https://docs.qq.com/pdf/DTFZGQXdTUXhIYWRq
>
> User Survey: https://forms.gle/w6Y6PiHTZr1nzbtWA
>
> 调查问卷(中文): https://wj.qq.com/s2/16150415/f50a/



> :warning: This project is in its early stages and is currently under **active development**.

> :warning: If you want to run the server remotely and access it on a different machine, the microphone on the front end will only launch in a secure context (a.k.a. https or localhost). See [MDN Web Doc](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia). Therefore, you should configure https with a reverse proxy to access the page on a remote machine (non-localhost).



## What is this project?


Open-LLM-VTuber is a voice to voice agent with voice interruption capability and a Live2D talking face running locally on your computer (offline mode available). 

It's your virtual girlfriend/boyfriend/pet/something_else running locally on macOS/Linux/Windows. Web frontend and electron frontend (with transparent background!) are available.

Long-term memory is temporily removed (will be added back very soon), but chat history persistence allows you to resume old conversations at any time.

This project supports a wide range of LLM backend, text-to-speech models, and speech recognition models. You can use your custom Live2D model by following the doc in `doc/live2d.md`. 

This project started as an attempt to recreate the closed-source AI VTuber `neuro-sama` with open-source alternatives that can run offline on platforms other than Windows.


<img width="500" alt="demo-image" src="https://github.com/t41372/Open-LLM-VTuber/assets/36402030/fa363492-7c01-47d8-915f-f12a3a95942c"/>



### Demo

English demo:





https://github.com/user-attachments/assets/f13b2f8e-160c-4e59-9bdb-9cfb6e57aca9


English Demo:
[YouTube](https://youtu.be/gJuPM_2qEZc)


中文 demo:

[BiliBili](https://www.bilibili.com/video/BV1krHUeRE98/), [YouTube](https://youtu.be/cb5anPTNklw)



## Why this project and not other similar projects on GitHub?
- It works on macOS and Linux
  - We care about macOS and Linux! And we also care about people who don't happen to use Nvidia GPU. Even if you don't have a GPU, you can choose to run things on CPU or offload demanding tasks to online APIs.
- Offline mode available
  - If you choose only the offline solutions, you don't have to connect to the internet. Just turn off your internet and be confident that nobody sees your chat log.
- You can interrupt the AI anytime with your voice without wearing headphones (or you may, of course). No, the AI won't heard itself.






### Some features we have
- [x] Chat with any LLM (Ollama, OpenAI, OpenAI compatible format, Gemini, Claude, Mistral, DeepSeek, Zhipu, running gguf directly, LM Studio, vLLM, and more!) by voice
- [x] A beautiful frontend with pet mode. Web and app frontend are both available.
- [x] Interrupt LLM with voice at any time
- [x] The AI can speak proactively (configurable)
- [x] Choose your own LLM backend, Speech Recognition, and TTS
- [x] Chat history persistence. You can resume old conversations.
- [x] Audio translation feature so that you can chat with AI in English while hearing a Japanese voice!
- [x] Works on macOS, Linux, and Windows
- [x] A rewritten codebase with many great features planned ahead! 



## Quick Start

[To be complete]

Read https://open-llm-vtuber.github.io/docs/quick-start for quick start. It will be translated to English once things are more stable.



### Update
> :warning: `v1.0.0` is a breaking change and requires re-deployment. You *may* still update via the method below (without the stash steps), but the configuration is incompatible and most of the dependencies needs to be reinstalled with `uv`. I recommend deploy this project again with the latest deployment guide.

[To be complete]

Run the upgrade script `python upgrade.py` to update.

or run the following command inside the project repository:

```sh
git stash push -u -m "Stashing all local changes"
git fetch
git pull
git stash pop
```




## Some other things

### Translation

Translation was implemented to let the program speak in a language different from the conversation language. For example, the LLM might be thinking in English, the subtitle is in English, and you are speaking English, but the voice of the LLM is in Japanese. This is achieved by translating the sentence before it's sent for audio generation.

[DeepLX](https://github.com/OwO-Network/DeepLX) is the only supported translation backend for now. You will need to deploy the deeplx service and set the configuration in `conf.yaml` to use it.

If you want to add more translation providers, they are in the `translate` directory, and the steps are very similar to adding new TTS or ASR providers.


### Enable Audio Translation

1. Set `TRANSLATE_AUDIO` in `conf.yaml` to True
2. Set `DEEPLX_TARGET_LANG` to your desired language. Make sure this language matches the language of the TTS speaker (for example, if the `DEEPLX_TARGET_LANG` is "JA", which is Japanese, the TTS should also be speaking Japanese.).






# Running in a Container [highly experimental]

:warning: This is highly experimental, but I think it works. Most of the time.

You can either build the image yourself or pull it from the docker hub. [![](https://img.shields.io/badge/t41372%2FOpen--LLM--VTuber-%25230db7ed.svg?logo=docker&logoColor=blue&labelColor=white&color=blue)](https://hub.docker.com/r/t41372/open-llm-vtuber)

- (but the image size is crazy large)
- The image on the docker hub might not updated as regularly as it can be. GitHub action can't build an image as big as this. I might look into other options.



Current issues:

- Large image size (~13GB) and will require more space because some models are optional and will be downloaded only when used.
- Nvidia GPU required (GPU passthrough limitation)
- [Nvidia Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) needs to be configured for GPU passthrough.
- Some models will have to be downloaded again if you stop the container. (will be fixed)
- Don't build the image on an Arm machine. One of the dependencies (grpc, to be exact) will fail for some reason https://github.com/grpc/grpc/issues/34998. 
- As mentioned before, you can't run it on a remote server unless the web page has https. That's because the web mic on the front end will only launch in a secure context (which means localhost or https environment only). 

Most of the ASR and TTS will be pre-installed. However, bark TTS and the original OpenAI Whisper (`Whisper`, not WhisperCPP) are NOT included in the default build process because they are huge (~8GB, which makes the whole container about 25GB). In addition, they don't deliver the best performance either. To include bark and/or whisper in the image, add the argument `--build-arg INSTALL_ORIGINAL_WHISPER=true --build-arg INSTALL_BARK=true` to the image build command.

Setup guide:

1. Review `conf.yaml` before building (currently burned into the image, I'm sorry):

2. Build the image:

 ```
 docker build -t open-llm-vtuber .
 ```

 (Grab a drink, this will take a while)

3. Grab a `conf.yaml` configuration file.
 Grab a `conf.yaml` file from this repo. Or you can get it directly from this [link](https://raw.githubusercontent.com/t41372/Open-LLM-VTuber/main/conf.yaml).

4. Run the container:

`$(pwd)/conf.yaml` should be the path of your `conf.yaml` file.

 ```
 docker run -it --net=host --rm -v $(pwd)/conf.yaml:/app/conf.yaml -p 12393:12393 open-llm-vtuber
 ```

5. Open localhost:12393 to test


# 🎉🎉🎉 Related Projects

[ylxmf2005/LLM-Live2D-Desktop-Assitant](https://github.com/ylxmf2005/LLM-Live2D-Desktop-Assitant)
- Your Live2D desktop assistant powered by LLM! Available for both Windows and MacOS, it senses your screen, retrieves clipboard content, and responds to voice commands with a unique voice. Featuring voice wake-up, singing capabilities, and full computer control for seamless interaction with your favorite character.



# 🛠️ Development
(this project is in the active prototyping stage, so many things will change)

Some abbreviations used in this project:

- LLM: Large Language Model
- TTS: Text-to-speech, Speech Synthesis, Voice Synthesis
- ASR: Automatic Speech Recognition, Speech recognition, Speech to text, STT
- VAD: Voice Activation Detection

### Regarding sample rates

You can assume that the sample rate is `16000` throughout this project.
The frontend stream chunks of `Float32Array` with a sample rate of `16000` to the backend.

### Add support for new TTS providers
1. Implement `TTSInterface` defined in `src/open_llm_vtuber/tts/tts_interface.py`.
2. Add your new TTS provider into `tts_factory`: the factory to instantiate and return the tts instance.
3. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your TTSEngine as kwargs.
4. Modify the `src/open_llm_vtuber/config_manager/tts.py` to add the configuration into the config validation pydantic model.

### Add support for new Speech Recognition provider
1. Implement `ASRInterface` defined in `src/open_llm_vtuber/asr/asr_interface.py`.
2. Add your new ASR provider into `asr_factory`: the factory to instantiate and return the ASR instance.
3. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your class as kwargs.
4. Modify the `src/open_llm_vtuber/config_manager/asr.py` to add the configuration into the pydantic model.

### Add support for new LLM provider (stateless)
1. Implement `LLMInterface` defined in `src/open_llm_vtuber/agent/stateless_llm/stateless_llm_interface.py`.
2. Add your new LLM provider into `llm_factory`: the factory to instantiate and return the LLM instance.
3. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your class as kwargs.
4. Modify the `src/open_llm_vtuber/config_manager/stateless_llm.py` to add the configuration into the config validation pydantic model.

### Add support for new Translation providers
1. Implement `TranslateInterface` defined in `src/open_llm_vtuber/translate/translate_interface.py`.
2. Add your new translation provider into `translate_factory`: the factory to instantiate and return the translator instance.
3. Add configuration to `conf.yaml`. The dict with the same name will be passed into the constructor of your translator as kwargs.
4. Modify the `src/open_llm_vtuber/config_manager/tts_preprocessor.py` to add the configuration into the config validation pydantic model.


# Acknowledgement
Awesome projects I learned from

- https://github.com/dnhkng/GlaDOS
- https://github.com/SchwabischesBauernbrot/unsuperior-ai-waifu
- https://codepen.io/guansss/pen/oNzoNoz
- https://github.com/Ikaros-521/AI-Vtuber
- https://github.com/zixiiu/Digital_Life_Server



## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=t41372/open-llm-vtuber&type=Date)](https://star-history.com/#t41372/open-llm-vtuber&Date)





