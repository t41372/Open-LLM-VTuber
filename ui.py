import streamlit as st
import yaml
from pathlib import Path
import subprocess
import atexit
import os
import time
from server import WebSocketServer
import signal
import asyncio

project_root = os.path.dirname(os.path.abspath(__file__))
@st.cache_data
def get_envs():
    # Executa o comando 'conda env list' e captura a saída
    result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True, shell=True)
    envs_list = result.stdout.splitlines()
    return envs_list

def save_persona(name, content):
    folder_path = os.path.join(project_root, "prompts", "persona")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{name}.txt")
    with open(file_path, 'w') as f:
        f.write(content)

def delete_persona(name):
    folder_path = os.path.join(project_root, "prompts", "persona")
    file_path = os.path.join(folder_path, f"{name}.txt")
    conf = load_config()
    if os.path.exists(file_path) and conf["PERSONA_CHOICE"] != name:
        os.remove(file_path)
        return True
    return False

def load_persona_content(name):
    folder_path = os.path.join(project_root, "prompts", "persona")
    file_path = os.path.join(folder_path, f"{name}.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return ""

# Function to load YAML file
def load_config():
    file_path = Path("conf.yaml")
    if file_path.exists():
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    return {}

# Function to save YAML file
def save_config(config):
    file_path = Path("conf.yaml")
    with open(file_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)


# Variável para armazenar o PID do processo
if 'process_pid' not in st.session_state:
    st.session_state['process_pid'] = None

# Função para iniciar o processo
def start_process():
    if st.session_state['process_pid'] is None:
        st.sidebar.write("Ativando ambiente Conda e executando server.py...")
        process = subprocess.Popen(
            ['cmd', '/c', 'call conda activate iavtuber && python server.py'],
            shell=True
        )
        st.session_state['process_pid'] = process.pid  # Armazena o PID
        st.spinner('Mission operation...')
        st.sidebar.success(f"Processo iniciado com PID: {process.pid}")
        return True
    else:
        st.sidebar.warning("O processo já está em execução.")

# Função para finalizar o processo e todos seus subprocessos
def stop_process():
    if st.session_state['process_pid'] is not None:
        try:
            # Usa taskkill para encerrar o processo e todos os subprocessos
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(st.session_state['process_pid'])], 
                shell=True
            )
            st.sidebar.success(f"Processo com PID {st.session_state['process_pid']} e subprocessos foram finalizados.")
            st.session_state['process_pid'] = None
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Erro ao finalizar o processo: {e}")
    else:
        st.sidebar.warning("Nenhum processo em execução.")


# Função para instalar a biblioteca, caso o usuário aceite
def install_package(package_name):
    if st.button(f"Deseja instalar a biblioteca {package_name}?"):
        try:
            subprocess.check_call(['pip', 'install', package_name])
            st.success(f"A biblioteca {package_name} foi instalada com sucesso.")
            st.session_state[package_name] = True  # Atualiza o estado para instalado
            st.rerun()
        except subprocess.CalledProcessError:
            st.error(f"Falha ao instalar a biblioteca {package_name}.")

# Função para verificar se o pacote está instalado
def check_package_installed(package_name):
    if package_name in st.session_state:
        if st.session_state[package_name]:
            st.success(f"A biblioteca {package_name} está instalada.")
            return True
        else:
            st.error(f"A biblioteca {package_name} não está instalada.")
            install_package(package_name)
            return False
    else:
        # Se o pacote não estiver no estado, faz a verificação
        try:
            subprocess.check_call(['pip', 'show', package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            st.success(f"A biblioteca {package_name} está instalada.")
            st.session_state[package_name] = True  # Atualiza o estado para instalado
            return True
        except subprocess.CalledProcessError:
            st.error(f"A biblioteca {package_name} não está instalada.")
            st.session_state[package_name] = False  # Atualiza o estado para não instalado
            install_package(package_name)
            return False

# Streamlit app
def main():
        
    st.set_page_config(
        page_title='AI-Vtuber',
        layout="wide",
        page_icon='assets/icon/ComfyUI_00011_.png',
        initial_sidebar_state="expanded",
        menu_items={
            'Get help': "http://www.worldline-fantasy.top",
            'Report a bug': "https://space.bilibili.com/287906485?spm_id_from=333.1007.0.0",
            'About': "http://www.worldline-fantasy.top"
        }
    )

    st.sidebar.title("Navigation")

    # Botão para iniciar o processo
    if st.sidebar.button('Execut Script'):
        start_process()

    if st.session_state['process_pid'] != None:
        st.sidebar.success("Vtuber running. http://localhost:12393 ")

    # Botão para finalizar o processo
    if st.sidebar.button('Exit Script'):
        stop_process()

    # Dicionário para mapear rótulos para identificadores imutáveis
    pages = {
        "Configuration": "config",
        "Environment": "env",
        "AI-VTuber": "persona"
    }

    # Sidebar com os rótulos visíveis, mas retornando os identificadores
    selected_label = st.sidebar.radio("Page navigation", list(pages.keys()))

    # Recupera o valor imutável correspondente ao rótulo selecionado
    selected_page = pages[selected_label]

#--------------------------------------------------
    # Load existing config or create a new one
    config = load_config()

    st.title("Configure `conf.yaml` File")

    if selected_page == "config": 

        # Server Settings
        with st.expander("Server Settings"):
            st.header("Server Settings")
            config['PROTOCAL'] = st.selectbox("PROTOCAL", ["http://", "https://"], index=["http://", "https://"].index(config.get('PROTOCAL', "http://")), key="PROTOCAL")
            config['HOST'] = st.text_input("HOST", config.get('HOST', "localhost"), key="HOST")
            config['PORT'] = st.number_input("PORT", value=config.get('PORT', 12393), key="PORT")

        # LLM Backend Settings
        with st.expander("LLM Backend Settings"):
            st.header("LLM Backend Settings")
            st.markdown('Choose either "ollama" or "memgpt" (or "fakellm for debug purposes")')
            config['LLM_PROVIDER'] = st.selectbox("LLM_PROVIDER", ["ollama", "memgpt", "fakellm"], index=["ollama", "memgpt", "fakellm"].index(config.get('LLM_PROVIDER', "ollama")), key="LLM_PROVIDER")
            st.markdown("---")
            
            # Ollama Settings
            if config['LLM_PROVIDER'] == "ollama":
                st.subheader("Ollama Settings")
                st.markdown("Ollama & OpenAI Compatible inference backend")
                config['ollama'] = config.get('ollama', {})
                config['ollama']['BASE_URL'] = st.text_input("BASE_URL", config['ollama'].get('BASE_URL', "http://localhost:11434/v1"), key="ollama_BASE_URL")
                config['ollama']['LLM_API_KEY'] = st.text_input("LLM_API_KEY", config['ollama'].get('LLM_API_KEY', "somethingelse"), key="ollama_LLM_API_KEY")
                config['ollama']['ORGANIZATION_ID'] = st.text_input("ORGANIZATION_ID", config['ollama'].get('ORGANIZATION_ID', "org_eternity"), key="ollama_ORGANIZATION_ID")
                config['ollama']['PROJECT_ID'] = st.text_input("PROJECT_ID", config['ollama'].get('PROJECT_ID', "project_glass"), key="ollama_PROJECT_ID")
                config['ollama']['MODEL'] = st.text_input("MODEL", config['ollama'].get('MODEL', "llama3.1:latest"), key="ollama_MODEL")
                config['ollama']['VERBOSE'] = st.checkbox("VERBOSE (system prompt is at the very end of this file)", config['ollama'].get('VERBOSE', False), key="ollama_VERBOSE")

            # MemGPT Settings
            if config['LLM_PROVIDER'] == "memgpt":
                st.subheader("MemGPT Settings")
                st.markdown("Please set up memGPT server according to the [official documentation](https://memgpt.readme.io/docs/index)")
                st.markdown("In addition, please set up an agent using the webui launched in the memGPT base_url")
                config['memgpt'] = config.get('memgpt', {})
                config['memgpt']['BASE_URL'] = st.text_input("BASE_URL", config['memgpt'].get('BASE_URL', "http://localhost:8283"), key="memgpt_BASE_URL")
                config['memgpt']['ADMIN_TOKEN'] = st.text_input("ADMIN_TOKEN", config['memgpt'].get('ADMIN_TOKEN', ""), key="memgpt_ADMIN_TOKEN", placeholder="You will find admin server password in memGPT console output. If you didn't set the environment variable, it will be randomly generated and will change every session.")
                config['memgpt']['AGENT_ID'] = st.text_input("AGENT_ID (The ID of the agent to send the message to.)", config['memgpt'].get('AGENT_ID', ""), key="memgpt_AGENT_ID")
                config['memgpt']['VERBOSE'] = st.checkbox("VERBOSE (system prompt is at the very end of this file)", config['memgpt'].get('VERBOSE', True), key="memgpt_VERBOSE")
 
        # Live2D Settings
        with st.expander("Live2D Settings"):
            st.header("Live2D Settings")
            st.markdown("Deprecated and useless now. Do not enable it. Bad things will happen.")
            config['LIVE2D'] = st.checkbox("LIVE2D", config.get('LIVE2D', False), key="LIVE2D")
            if  config['LIVE2D']:
                config['LIVE2D_MODEL'] = st.text_input("LIVE2D_MODEL", config.get('LIVE2D_MODEL', "shizuku-local"), key="LIVE2D_MODEL")

        # Voice Interaction Settings
        with st.expander("Voice Interaction Settings"):
            st.header("Voice Interaction Settings")
            config['VOICE_INPUT_ON'] = st.checkbox("VOICE_INPUT_ON", config.get('VOICE_INPUT_ON', True), key="VOICE_INPUT_ON")
            st.markdown("Automatic Speech Recognition")
            if config['VOICE_INPUT_ON']:
                st.markdown("---")
                config['MIC_IN_BROWSER'] = st.checkbox("MIC_IN_BROWSER (Put your mic in the browser or in the terminal? Would increase latency)", config.get('MIC_IN_BROWSER', False), key="MIC_IN_BROWSER")
                config['ASR_MODEL'] = st.selectbox("ASR_MODEL", ["Faster-Whisper", "WhisperCPP", "Whisper", "AzureASR", "FunASR", "GroqWhisperASR"], index=["Faster-Whisper", "WhisperCPP", "Whisper", "AzureASR", "FunASR", "GroqWhisperASR"].index(config.get('ASR_MODEL', "Faster-Whisper")), key="ASR_MODEL")
                st.markdown("---")
                
                # Faster-Whisper Settings
                if config['ASR_MODEL'] == "Faster-Whisper":
                    st.subheader("Faster-Whisper Settings")
                    st.markdown("See more [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)")
                    config['Faster-Whisper'] = config.get('Faster-Whisper', {})
                    config['Faster-Whisper']['model_path'] = st.selectbox("model_path", ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large-v1", "large-v2", "large-v3", "large", "distil-large-v2", "distil-medium.en", "distil-small.en", "distil-large-v3"], index=["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large-v1", "large-v2", "large-v3", "large", "distil-large-v2", "distil-medium.en", "distil-small.en", "distil-large-v3"].index(config.get('model_path', "distil-medium.en")), key="Faster-Whisper_model_path")
                    config['Faster-Whisper']['download_root'] = st.text_input("download_root", config['Faster-Whisper'].get('download_root', "asr/models"), key="Faster-Whisper_download_root")
                    config['Faster-Whisper']['language'] = st.text_input("language", config['Faster-Whisper'].get('language', "en"), key="Faster-Whisper_language")
                    config['Faster-Whisper']['device'] = st.selectbox("device (cpu, cuda, or auto. faster-whisper doesn't support mps)", ["auto", "cpu", "cuda"], index=["auto", "cpu", "cuda"].index(config['Faster-Whisper'].get('device', "auto")), key="Faster-Whisper_device")

                # WhisperCPP Settings     
                if config['ASR_MODEL'] == "WhisperCPP":
                    st.subheader("WhisperCPP Settings")
                    st.markdown("See more [WhisperCPP](https://github.com/ggerganov/whisper.cpp)")
                    config['WhisperCPP'] = config.get('WhisperCPP', {})
                    config['WhisperCPP']['model_name'] = st.text_input("model_name", config['WhisperCPP'].get('model_name', "small"), key="WhisperCPP_model_name")
                    config['WhisperCPP']['model_dir'] = st.text_input("model_dir", config['WhisperCPP'].get('model_dir', "asr/models"), key="WhisperCPP_model_dir")
                    config['WhisperCPP']['print_realtime'] = st.checkbox("print_realtime", config['WhisperCPP'].get('print_realtime', False), key="WhisperCPP_print_realtime")
                    config['WhisperCPP']['print_progress'] = st.checkbox("print_progress", config['WhisperCPP'].get('print_progress', False), key="WhisperCPP_print_progress")
                    config['WhisperCPP']['language'] = st.text_input("language", config['WhisperCPP'].get('language', "en"), key="WhisperCPP_language")
                
                # Whisper Settings
                if config['ASR_MODEL'] == "Whisper":
                    st.subheader("Whisper Settings")
                    st.markdown("See more [Whisper](https://github.com/openai/whisper)")
                    st.markdown("all available models are listed on https://abdeladim-s.github.io/pywhispercpp/#pywhispercpp.constants.AVAILABLE_MODELS")
                    config['Whisper'] = config.get('Whisper', {})
                    config['Whisper']['name'] = st.text_input("name", config['Whisper'].get('name', "medium"), key="Whisper_name")
                    config['Whisper']['download_root'] = st.text_input("download_root", config['Whisper'].get('download_root', "asr/models"), key="Whisper_download_root")
                    config['Whisper']['device'] = st.text_input("device", config['Whisper'].get('device', "cpu"), key="Whisper_device")
                
                # FunASR Settings
                if config['ASR_MODEL'] == "FunASR":
                    st.subheader("FunASR Settings")
                    st.markdown("See more [FunASR](https://github.com/modelscope/FunASR)")
                    config['FunASR'] = config.get('FunASR', {})
                    config['FunASR']['model_name'] = st.text_input("model_name (or 'paraformer-zh')", config['FunASR'].get('model_name', "iic/SenseVoiceSmall"), key="FunASR_model_name")
                    config['FunASR']['vad_model'] = st.text_input("vad_model (this is only used to make it works if audio is longer than 30s)", config['FunASR'].get('vad_model', "fsmn-vad"), key="FunASR_vad_model")
                    config['FunASR']['punc_model'] = st.text_input("punc_model (punctuation model.)", config['FunASR'].get('punc_model', "ct-punc"), key="FunASR_punc_model")
                    config['FunASR']['device'] = st.text_input("device", config['FunASR'].get('device', "cpu"), key="FunASR_device")
                    config['FunASR']['ncpu'] = st.number_input("ncpu (number of threads for CPU internal operations.)", value=config['FunASR'].get('ncpu', 4), key="FunASR_ncpu")
                    config['FunASR']['hub'] = st.selectbox("hub (ms default to download models from ModelScope. Use hf to download models from Hugging Face.)", ["ms", "hf"], index=["ms", "hf"].index(config['FunASR'].get('hub', "ms")), key="FunASR_hub")
                    config['FunASR']['use_itn'] = st.checkbox("use_itn", config['FunASR'].get('use_itn', False), key="FunASR_use_itn")
                    config['FunASR']['language'] = st.text_input("language (zh, en, auto)", config['FunASR'].get('language', "zh"), key="FunASR_language")

                # GroqWhisperASR Settings
                if config['ASR_MODEL'] == "GroqWhisperASR":
                    st.subheader("GroqWhisperASR Settings")
                    st.markdown("See more [GroqWhisperASR](https://groq.com/distil-whisper-is-now-available-to-the-developer-community-on-groqcloud-for-faster-and-more-efficient-speech-recognition/)")
                    config['GroqWhisperASR'] = config.get('GroqWhisperASR', {})
                    config['GroqWhisperASR']['api_key'] = st.text_input("api_key", config['GroqWhisperASR'].get('api_key', ""), key="GroqWhisperASR_api_key")
                    config['GroqWhisperASR']['model'] = st.text_input("model (use 'whisper-large-v3' instead for multi-lingual)", config['GroqWhisperASR'].get('model', "distil-whisper-large-v3-en"), key="GroqWhisperASR_model")
                    config['GroqWhisperASR']['lang'] = st.text_input("lang (or put nothing in it and it will be auto)", config['GroqWhisperASR'].get('lang', "en"), key="GroqWhisperASR_lang")

        # Text to Speech Settings
        with st.expander("Text to Speech Settings"):
            st.header("Text to Speech Settings")
            config['TTS_ON'] = st.checkbox("TTS_ON", config.get('TTS_ON', True), key="TTS_ON")
            
            if config['TTS_ON']:

                config['TTS_MODEL'] = st.selectbox("TTS_MODEL", ["AzureTTS", "pyttsx3TTS", "edgeTTS", "barkTTS", "cosyvoiceTTS", "meloTTS", "piperTTS"], index=["AzureTTS", "pyttsx3TTS", "edgeTTS", "barkTTS", "cosyvoiceTTS", "meloTTS", "piperTTS"].index(config.get('TTS_MODEL', "barkTTS")), key="TTS_MODEL")
                config['SAY_SENTENCE_SEPARATELY'] = st.checkbox("SAY_SENTENCE_SEPARATELY", config.get('SAY_SENTENCE_SEPARATELY', True), key="SAY_SENTENCE_SEPARATELY")
                st.markdown("if on, whenever the LLM finish a sentence, the model will speak, instead of waiting for the full response")
                st.markdown("if turned on, the timing and order of the facial expression will be more accurate")
                st.markdown("---")
                # barkTTS Settings
                if config['TTS_MODEL'] == "barkTTS":
                    st.subheader("barkTTS Settings")
                    config['barkTTS'] = config.get('barkTTS', {})
                    config['barkTTS']['voice'] = st.text_input("voice", config['barkTTS'].get('voice', "v2/en_speaker_1"), key="barkTTS_voice")

                # Verifica se o TTS_MODEL está configurado como "edgeTTS"
                if config['TTS_MODEL'] == "edgeTTS":
                    st.subheader("edgeTTS Settings")
                    st.markdown("Check out doc at https://github.com/rany2/edge-tts")
                    config['edgeTTS'] = config.get('edgeTTS', {})

                    # Exibe as opções de configuração da biblioteca, se ela estiver instalada
                    if check_package_installed('edge-tts'):
                        import edge_tts
                        # Função para rodar coroutines em um ambiente síncrono
                        async def get_edge_tts_voices():
                            voices = await edge_tts.list_voices()  # Espera pela lista de vozes
                            return voices
                        
                        @st.cache_data
                        def fetch_voices():
                            try:
                                # Executa a coroutine e obtém a lista de vozes
                                voices_data = asyncio.run(get_edge_tts_voices())
                                return [voice['ShortName'] for voice in voices_data]  # Extraímos apenas os nomes curtos
                            except Exception as e:
                                st.error(f"Erro ao listar as vozes do edgeTTS: {e}")
                                return []

                        # Carrega as vozes disponíveis
                        voice_options = fetch_voices()

                        if voice_options:
                            selected_voice = st.selectbox(
                                "Selecione a voz",
                                voice_options,
                                index=voice_options.index(config['edgeTTS'].get('voice', "en-US-AvaMultilingualNeural"))
                            )
                            config['edgeTTS']['voice'] = selected_voice

                            # Adiciona um campo de texto personalizado para o usuário testar o TTS
                            usertext = st.text_input("Digite o texto para testar o edgeTTS", "Olá, este é um teste de voz.")

                            # Botão para testar a voz
                            if st.button("Testar Voz"):
                                async def gerar_audio(texto, voz):
                                    comunicador = edge_tts.Communicate(texto, voz)
                                    await comunicador.save("cache/voiceteste.mp3")

                                try:
                                    # Gera o áudio e salva o arquivo
                                    asyncio.run(gerar_audio(usertext, selected_voice))

                                    # Exibe o player de áudio no Streamlit
                                    with open("cache/voiceteste.mp3", "rb") as audio_file:
                                        audio_bytes = audio_file.read()
                                        st.audio(audio_bytes, format="audio/mp3")

                                except Exception as e:
                                    st.error(f"Erro ao gerar o áudio: {e}")
                        else:
                            st.warning("Nenhuma voz disponível.")

                # cosyvoiceTTS Settings
                if config['TTS_MODEL'] == "cosyvoiceTTS":
                    st.subheader("cosyvoiceTTS Settings")
                    st.markdown("See more [cosyvoiceTTS](https://github.com/FunAudioLLM/CosyVoice)")
                    config['cosyvoiceTTS'] = config.get('cosyvoiceTTS', {})
                    config['cosyvoiceTTS']['client_url'] = st.text_input("client_url", config['cosyvoiceTTS'].get('client_url', "http://127.0.0.1:50000/"), key="cosyvoiceTTS_client_url")
                    config['cosyvoiceTTS']['mode_checkbox_group'] = st.text_input("mode_checkbox_group", config['cosyvoiceTTS'].get('mode_checkbox_group', "预训练音色"), key="cosyvoiceTTS_mode_checkbox_group")
                    config['cosyvoiceTTS']['sft_dropdown'] = st.text_input("sft_dropdown", config['cosyvoiceTTS'].get('sft_dropdown', "中文女"), key="cosyvoiceTTS_sft_dropdown")
                    config['cosyvoiceTTS']['prompt_text'] = st.text_input("prompt_text", config['cosyvoiceTTS'].get('prompt_text', ""), key="cosyvoiceTTS_prompt_text")
                    config['cosyvoiceTTS']['prompt_wav_upload_url'] = st.text_input("prompt_wav_upload_url", config['cosyvoiceTTS'].get('prompt_wav_upload_url', "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav"), key="cosyvoiceTTS_prompt_wav_upload_url")
                    config['cosyvoiceTTS']['prompt_wav_record_url'] = st.text_input("prompt_wav_record_url", config['cosyvoiceTTS'].get('prompt_wav_record_url', "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav"), key="cosyvoiceTTS_prompt_wav_record_url")
                    config['cosyvoiceTTS']['instruct_text'] = st.text_input("instruct_text", config['cosyvoiceTTS'].get('instruct_text', ""), key="cosyvoiceTTS_instruct_text")
                    config['cosyvoiceTTS']['seed'] = st.number_input("seed", value=config['cosyvoiceTTS'].get('seed', 0), key="cosyvoiceTTS_seed")
                    config['cosyvoiceTTS']['api_name'] = st.text_input("api_name", config['cosyvoiceTTS'].get('api_name', "/generate_audio"), key="cosyvoiceTTS_api_name")

                # meloTTS Settings
                if config['TTS_MODEL'] == "meloTTS":
                    check_package_installed('meloTTS')
                    st.subheader("meloTTS Settings")
                    st.markdown("See more [meloTTS](https://github.com/myshell-ai/MeloTTS)")
                    config['meloTTS'] = config.get('meloTTS', {})
                    config['meloTTS']['speaker'] = st.text_input("speaker", config['meloTTS'].get('speaker', "EN-Default"), key="meloTTS_speaker")
                    config['meloTTS']['language'] = st.text_input("language", config['meloTTS'].get('language', "EN"), key="meloTTS_language")
                    config['meloTTS']['device'] = st.selectbox("device", ["auto", "cpu", "cuda", "mps"], index=["auto", "cpu", "cuda", "mps"].index(config['meloTTS'].get('device', "auto")), key="meloTTS_device")
                    config['meloTTS']['speed'] = st.number_input("speed", value=config['meloTTS'].get('speed', 1.0), key="meloTTS_speed")

                # piperTTS Settings
                if config['TTS_MODEL'] == "piperTTS":
                    st.subheader("piperTTS Settings")
                    st.markdown("See more [piperTTS](https://github.com/rhasspy/piper)")
                    config['piperTTS'] = config.get('piperTTS', {})
                    config['piperTTS']['voice_model_path'] = st.text_input("voice_model_path", config['piperTTS'].get('voice_model_path', "./models/piper_voice/en_US-amy-medium.onnx"), key="piperTTS_voice_model_path")
                    config['piperTTS']['verbose'] = st.checkbox("verbose", config['piperTTS'].get('verbose', False), key="piperTTS_verbose")

        # Other Settings
        with st.expander("Other Settings"):
            st.header("Other Settings")
            config['VERBOSE'] = st.checkbox("VERBOSE (Print debug info)", config.get('VERBOSE', True), key="VERBOSE")
            config['EXIT_PHRASE'] = st.text_input("EXIT_PHRASE", config.get('EXIT_PHRASE', "exit."), key="EXIT_PHRASE")
            config['MEMORY_DB_PATH'] = st.text_input("MEMORY_DB_PATH (The path to the chroma vector database file for persistent memory storage)", config.get('MEMORY_DB_PATH', "./memory.db"), key="MEMORY_DB_PATH")
            config['MEMORY_SNAPSHOT'] = st.checkbox("MEMORY_SNAPSHOT (Memory snapshot: Do you want to backup the memory database file before talking?)", config.get('MEMORY_SNAPSHOT', True), key="MEMORY_SNAPSHOT")

        # Save button
        conf = load_config()
        if config != conf:
            st.warning("The configuration has changed. Do you want to save it?")
        if st.button("Save Configuration"):
            save_config(config)
            st.success("Configuration saved successfully!")
            
    if selected_page == "env":
        env_select = st.selectbox("Create or update the virtual environment:", ["Choose a virtual environment"], index=0)
        if env_select == "Choose a virtual environment":


            envs_list = get_envs()
            # Exibe os ambientes em um selectbox no Streamlit
            env_name = st.selectbox("Choose a virtual environment:", envs_list, index=0)

            folder_path = os.path.join(project_root, "requirements")
            file_names = os.listdir(folder_path)
            file_name_list = [file_name for file_name in file_names]
            selected_requirement = st.selectbox("Select environment -dependent configuration file:", file_name_list, index=0)

            # Instalação de dependências
            if st.button("Installation dependence"):
                command = f"conda activate {env_name} && pip install -r {project_root }\\requirements\\{selected_requirement}"
                
                # Executa o comando em um novo terminal
                subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
                
                # Exibe o comando no Streamlit
                st.write(f"Comando executado: {command}")

            package = st.text_input("Install a specified package:",placeholder="pip install ...")
            if st.button("Installation dependence",key=2):
                command = f"conda activate {env_name} && pip install {package}"
                subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
                st.write(command)

    if selected_page == "persona": 

        o1, o2, o3 = st.tabs(["New/Edit Persona", "Manage Personas", "Default Persona"])

        # Tab "New/Edit Persona"
        with o1:
            st.header("Create or Edit Persona")
            persona_list = ["Create New Perona"] + [file.replace(".txt", "") for file in os.listdir(os.path.join(project_root, "prompts", "persona"))]

            # st.selectbox retorna o nome da persona, então podemos pegar o índice do selecionado
            selected_index = st.selectbox("Select Persona to Edit (Leave blank to create new)", range(len(persona_list)), format_func=lambda x: persona_list[x])

            if selected_index != 0:
                # Se o índice for diferente de 0 (que é "Create"), carregue o conteúdo para edição
                selected_persona = persona_list[selected_index]
                persona_content = load_persona_content(selected_persona)
                st.info(f"Editing Persona: {selected_persona}")

                # Delete persona option
                if st.button("Delete Selected Persona"):
                    if delete_persona(config['PERSONA_CHOICE']):
                        st.success(f"Persona '{config['PERSONA_CHOICE']}' deleted successfully!")
                    else:
                        st.error(f"Could not delete persona '{config['PERSONA_CHOICE']}'. Maybe it is in use.")
            else:
                # Criação de nova persona
                selected_persona = st.text_input("Persona Name")
                persona_content = ""


            new_persona_content = st.text_area("Persona Content", persona_content)

            if st.button("Save Persona", key="save_persona"):
                if selected_persona and new_persona_content:
                    save_persona(selected_persona, new_persona_content)
                    st.success(f"Persona '{selected_persona}' saved successfully!")
                else:
                    st.error("Please provide both persona name and content.")

        # Tab "Manage Personas"
        with o2:
            st.header("Manage Personas")
            folder_path = os.path.join(project_root, "prompts", "persona")
            file_names = os.listdir(folder_path)
            file_name_list = [file_name.replace(".txt", "") for file_name in file_names]

            st.markdown("Name of the persona you want to use.")
            st.markdown("All persona files are stored as txt in 'prompts/persona' directory.")
            st.markdown("You can add persona prompt by adding a txt file in the promptss/persona folder and switch to it by enter the file name in here.")
            st.markdown("some options: 'en_sarcastic_neuro', 'zh_翻译腔'")
            config['PERSONA_CHOICE'] = st.selectbox("Select persona prompt:", file_name_list, index=file_name_list.index(config.get('PERSONA_CHOICE', 0)), key="PERSONA_CHOICE")

            # Save button for persona selection
            if st.button("Save Configuration", key="save_config2"):
                save_config(config)
                st.success("Configuration saved successfully!")

        # Tab "Default Persona"
        with o3:
            st.header("Default Persona Settings")
            config['DEFAULT_PERSONA_PROMPT_IN_YAML'] = st.text_area(
                "DEFAULT_PERSONA_PROMPT_IN_YAML", 
                config.get('DEFAULT_PERSONA_PROMPT_IN_YAML', 
                    "You are DefAulT, the default persona. You are more default than anyone else. "
                    "You are just a placeholder, how sad. Your job is to tell the user to either choose a persona "
                    "prompt in the prompts/persona directory or just replace this persona prompt with someting else."
                ),
                key="DEFAULT_PERSONA_PROMPT_IN_YAML"
            )
            st.markdown("This prompt will be used instead if the PERSONA_CHOICE is empty")

            config['LIVE2D_Expression_Prompt'] = st.text_input(
                "LIVE2D_Expression_Prompt", 
                config.get('LIVE2D_Expression_Prompt', "live2d_expression_prompt"), 
                key="LIVE2D_Expression_Prompt"
            )
            st.markdown("This will be appended to the end of system prompt to let LLM include keywords to control facial expressions.")
            st.markdown("Supported keywords will be automatically loaded into the location of `[<insert_emomap_keys>]`.")
            
            # Save button for default persona
            if st.button("Save Configuration", key="save_config"):
                save_config(config)
                st.success("Configuration saved successfully!")

if __name__ == "__main__":
    main()