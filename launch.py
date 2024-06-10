# new version of main.py



import sys
import importlib
# from rich import print
import yaml
from Ollama import Ollama
import api_keys
import requests

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
            "pyttsx3TTS": "tts.pyttsx3TTS"
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

def callLLM(text, llm, tts):
    rag_on = get_config("RAG_ON", False)
    result = llm.generateWithLongTermMemory(prompt=text) if rag_on else llm.generateWithMemory(text)
    # print(result)
    send_message_to_broadcast(result)
    if get_config("TTS_ON", False):
        tts.speak(result)




def send_message_to_broadcast(message):
    url = "http://127.0.0.1:8000/broadcast"
    data = {"message": message}
    response = requests.post(url, json=data)
    print(f"Response Status Code: {response.status_code}")
    if response.ok:
        print("Message successfully sent to the broadcast route.")
    else:
        print("Failed to send message to the broadcast route.")






if __name__ == "__main__":
    try:
        
        system_prompt = get_config("SYSTEM_PROMPT")
        if get_config("LIVE2D"):
            system_prompt += get_config("LIVE2D_Expression_Prompt")
        
        if get_config("VERBOSE", default=False):
            print("\n === System Prompt ===") 
            print(system_prompt)

        llm = Ollama(base_url=get_config("BASE_URL"), verbose=get_config("VERBOSE", False), model=get_config("MODEL"), system=system_prompt, vector_db_path=get_config("MEMORY_DB_PATH"))
        speech2text, tts = init_speech_services()
        interaction_mode(llm, speech2text, tts)
    except Exception as e:
        print(f"Error initializing: {e}")
        sys.exit(1)


