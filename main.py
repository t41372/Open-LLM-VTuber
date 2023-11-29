
from Ollama import Ollama
import text2speech 
import speech2text
from dotenv import load_dotenv
import utils
import os
import sys

from datetime import datetime
now = datetime.now()

load_dotenv()  # take environment variables from .

CURRENT_SESSION_ID = now.strftime("%Y-%m-%d-%H-%M-%S")

SAVE_CHAT_HISTORY = (os.getenv("SAVE_CHAT_HISTORY") == "True")

CHAT_HISTORY_DIR = os.getenv("CHAT_HISTORY_DIR")

EXIT_PHRASE = os.getenv("EXIT_PHRASE")

MEMORY_SNAPSHOT = (os.getenv("MEMORY_SNAPSHOT") == "True")

MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH")

TTS_ON = (os.getenv("TTS_ON") == "True")

VOICE_INPUT_ON = (os.getenv("VOICE_INPUT_ON") == "True")

RAG_ON = (os.getenv("RAG_ON") == "True")

EXTRA_SYSTEM_PROMPT_RAG = os.getenv("EXTRA_SYSTEM_PROMPT_RAG")

LLMASSIST_RAG_ON = (os.getenv("LLMASSIST_RAG_ON") == "True")

def textInteractionMode(llm:Ollama):
    '''
    interact with the llm in text mode, but with speech output
    '''
    while True:
        user_input = input(">> ")
        if user_input.lower() == EXIT_PHRASE.lower():
            print("Exiting...")
            break
        else:
            callLLM(user_input, llm)

def speechInteractionMode(llm:Ollama):
    '''
    Lauch the speech to text service and interact with the llm in speech mode.
    The function callbackToLLM is the callback function when a sentence is recognized.
    '''
    # The commented code below is for continuous speech to text service.
    # The recognizer will listen to you even when the llm is talking (so it can hear itself...)
    # Not recommended if you are using the speaker
    # recognitionResult = launchContinuousSpeech2TextService(callLLM)

    while True:
        recognitionResult = speech2text.speech2TextOnce()
        if recognitionResult.strip().lower().replace(".", "") == EXIT_PHRASE.lower():
            print("Exiting...")
            
            return
        elif(recognitionResult != ""):
            print("\nUser Input: \n" + recognitionResult + "\n\nAI Response: \n")
            callLLM(recognitionResult, llm)
            print("======\n")
    


def callLLM(text, llm:Ollama, verbose=False, saveChatHistory=SAVE_CHAT_HISTORY, 
            chatHistoryDir=CHAT_HISTORY_DIR, ttsOn=TTS_ON, ragOn=RAG_ON, llmAssistRagOn=LLMASSIST_RAG_ON):
        '''
        Call the llm with text and print the result.
        text: str
            the text that is recognized
        '''
        if ragOn:
            print(">> RAG is on. Generating response with RAG...")
            result = llm.generateWithLongTermMemory(prompt=text, vector_db=MEMORY_DB_PATH, system=llm.system + EXTRA_SYSTEM_PROMPT_RAG, LLMAssist=llmAssistRagOn)
        else: 
            print(">> RAG is off. Generating response without RAG...")
            result = llm.generateWithMemory(text)

        print("\n\n>> Curent Token Count: {}".format(len(llm.context)))

        if verbose:
            print(">> Results: \n")
            print(result)

        if saveChatHistory:
            message = "User: \n" + text + "\n\n" + "AI: \n" + result + "\n\n"
            utils.messageLogger(message, chatHistoryDir, CURRENT_SESSION_ID + ".txt")

        if ttsOn:
            text2speech.speak(result)
        print("\n")


# =======

if __name__ == "__main__":

    # load parameters and instantiate the ollama
    try:
        llm = Ollama(
            base_url=os.getenv("BASE_URL"),
            verbose=(os.getenv("VERBOSE") == "True"),
            model=os.getenv("MODEL"),
            system= os.getenv("SYSTEM_PROMPT"),
            vector_db_path=os.getenv("MEMORY_DB_PATH")
        )
    except Exception as e:
        print("Error: Missing or invalid environment variables. Please check your configuration.")
        print(f"Exception: {str(e)}")
        sys.exit(1)


    # save a snapshot of the memory

    if MEMORY_SNAPSHOT:
        backUpFilePath = utils.backUpFile(MEMORY_DB_PATH)
        print(">>> Memory snapshot saved at " + MEMORY_DB_PATH + ".bk")

    # speechInteractionMode(llm)
    if VOICE_INPUT_ON:
        speechInteractionMode(llm)
    else:
        textInteractionMode(llm)

    if MEMORY_SNAPSHOT:
        revertMemory = input("\n------------\n\n>>> Save this conversation to long term memory? (Y/n)")
        if revertMemory == "n":
            utils.restoreFile(MEMORY_DB_PATH, backUpFilePath)
            print(">>> Memory reverted. This conversation never took place.")
            print(">>> But in case you need it, the message log is still saved at " + CHAT_HISTORY_DIR + "" + CURRENT_SESSION_ID + ".txt")
        else:
            print(">>> LLM will remember this conversation.")
            print(">>> But if you change your mind, replace the memory file with " + backUpFilePath)
    
    #  textInteractionMode()

    
