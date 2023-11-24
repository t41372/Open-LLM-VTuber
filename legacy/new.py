from langchain.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .

# load the environment variables
VERBOSE = os.getenv("VERBOSE")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
AI_ROLE = "You are an unhelpful and sarcastic AI that makes fun of humans. You are having a conversation with a human."

llm = Ollama(
    base_url=BASE_URL,
    verbose= False,
    model=MODEL,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
)

while True:
    llm(input("\n>> "))