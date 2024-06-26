# new version of main.py



import json
import importlib
from Ollama import Ollama as oldOllama
from llm.ollama import LLM
import api_keys
import requests
from live2d import Live2dController

import yaml
# Load configurations
def load_config():
    with open('conf.yaml', 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Simplified configuration access
def get_config(key, default=None):
    return config.get(key, default)

# Load and return module
def load_module(module_name):
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        print(f"Module {module_name} not found: {e}")
        return None


# initialize live2d
def init_live2d():
    live2d_on = get_config("LIVE2D", False)
    if live2d_on:
        live2d_model = get_config("LIVE2D_MODEL")
        
        url = f"{get_config('PROTOCOL', 'http://')}{get_config('HOST', 'localhost')}:{get_config('PORT', 8000)}"
        live2d_controller = Live2dController(live2d_model, base_url=url)
        return live2d_controller
    return None

live2d = init_live2d()


def init_llm():

    if get_config("RAG_ON", False): 
        llm = oldOllama(base_url=get_config("BASE_URL"), verbose=get_config("VERBOSE", False), model=get_config("MODEL"), system=system_prompt, vector_db_path=get_config("MEMORY_DB_PATH"))
        return llm

    llm_provider = get_config("LLM_PROVIDER")
    llm_module_name = {
        "ollama": "llm.ollama",
        "memgpt": "llm.memGPT",
    }.get(llm_provider)
    llm = load_module(llm_module_name)

    if llm_provider == "ollama":
        llm = LLM(
            base_url=get_config("BASE_URL") + "/v1", 
            verbose=get_config("VERBOSE", False), 
            model=get_config("MODEL"), 
            system=system_prompt, 
            llm_api_key=get_config("LLM_API_KEY"),
            project_id=get_config("PROJECT_ID"),
            organization_id=get_config("ORGANIZATION_ID"))
    elif llm_provider == "memgpt":
        llm = llm.LLM()

    return llm


# Initialize speech to text and text to speech
def init_speech_services():
    voice_input_on = get_config("VOICE_INPUT_ON", False)
    tts_on = get_config("TTS_ON", False)
    speech2text, tts = None, None

    if voice_input_on:
        stt_model = get_config("STT_MODEL")
        stt_module_name = {
            "Faster-Whisper": "speech2text.faster-whisper.voice_recognition",
            "AzureSTT": "speech2text.azureSTT"
        }.get(stt_model)
        speech2text = load_module(stt_module_name)
        if speech2text and stt_model == "AzureSTT":
            speech2text = speech2text.VoiceRecognition(callbackFunction=print, subscription_key=api_keys.AZURE_API_Key, region=api_keys.AZURE_REGION)
        else:
            speech2text = speech2text.VoiceRecognition()

    if tts_on:
        tts_model = get_config("TTS_MODEL", "pyttsx3TTS")
        tts_module_name = {
            "AzureTTS": "tts.azureTTS",
            "pyttsx3TTS": "tts.pyttsx3TTS",
            "edgeTTS": "tts.edgeTTS",
            "barkTTS": "tts.barkTTS",
        }.get(tts_model, "tts.pyttsx3TTS")
        tts = load_module(tts_module_name)
        if tts and tts_model == "AzureTTS":
            tts = tts.TTSEngine(sub_key=api_keys.AZURE_API_Key, region=api_keys.AZURE_REGION, voice=api_keys.AZURE_VOICE)
        else:
            tts = tts.TTSEngine()

    return speech2text, tts

# Interaction modes
def interaction_mode(llm, speech2text, tts):
    exit_phrase = get_config("EXIT_PHRASE", "exit").lower()
    voice_input_on = get_config("VOICE_INPUT_ON", False)

    while True:
        user_input = speech2text.transcribe_once() if voice_input_on else input(">> ")
        if user_input.strip().lower() == exit_phrase:
            print("Exiting...")
            break
        callLLM(user_input, llm, tts)
    

def generate_audio_file(sentence, file_name_no_ext):
    '''
    Generate audio file from the given sentence.
    sentence: str
        the sentence to generate audio from
    file_name_no_ext: str
        name of the file without extension
        
        Returns:
        str: the path to the generated audio file. 
        None if TTS is off or the sentence is empty.
        
    '''

    print("generate...")

    if not get_config("TTS_ON", False):
        return None
    
    if live2d:
        sentence = live2d.remove_expression_from_string(sentence)

    if sentence.strip() == "":
        return None

    return tts.generate_audio(sentence, 
                       file_name_no_ext=file_name_no_ext
                       )

def stream_audio_file(sentence, filename):
    '''
    Stream the audio file to the frontend and wait for the audio to finish. The audio and the data to control the mouth movement will be sent to the live2d frontend.
    
    sentence: str
        the sentence to speak
    filename: str
        the path of the audio file to stream
    '''
    print("stream...")

    if not live2d:
        tts.speak(sentence)
        return
    
    if live2d.remove_expression_from_string(sentence).strip() == "":
        live2d.check_string_for_expression(sentence, send_delay=0)
        live2d.send_text(sentence)
        return

    
    live2d.send_text(sentence)
    
    # if tts.stream_audio_file and callable(tts.stream_audio_file):
    tts.stream_audio_file(filename, 
        on_speak_start_callback=lambda: live2d.check_string_for_expression(sentence))




def callLLM(text, llm, tts):
    rag_on = get_config("RAG_ON", False)

    if not get_config("TTS_ON", False):
        llm.chat_stream_audio(text)
        return

    if rag_on:
        result = llm.generateWithLongTermMemory(prompt=text)
        stream_audio_file(result, generate_audio_file(result, "temp"))
    elif get_config("SAY_SENTENCE_SEPARATELY", False):
        result = llm.chat_stream_audio(text, 
                          generate_audio_file=generate_audio_file, stream_audio_file=stream_audio_file)
    else:
        result = llm.chat_stream_audio(text)
        stream_audio_file(result, generate_audio_file(result, "temp"))



def send_message_to_broadcast(message):
    url = "http://127.0.0.1:8000/broadcast"
    
    payload = json.dumps(message)

    response = requests.post(url, json={"message": payload})
    print(f"Response Status Code: {response.status_code}")
    if response.ok:
        print("Message successfully sent to the broadcast route.")
    else:
        print("Failed to send message to the broadcast route.")






if __name__ == "__main__":


    try:
        
        system_prompt = get_config("SYSTEM_PROMPT")
        if get_config("LIVE2D"):
            system_prompt += get_config("LIVE2D_Expression_Prompt").replace("[<insert_emomap_keys>]", live2d.getEmoMapKeyAsString())
        
        if get_config("VERBOSE", default=False):
            print("\n === System Prompt ===") 
            print(system_prompt)

        
        llm = init_llm()


        speech2text, tts = init_speech_services()
        interaction_mode(llm, speech2text, tts)
    except Exception as e:
        print(f"Error initializing: {e}")
        raise
        # sys.exit(1)


