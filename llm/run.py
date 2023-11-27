
from Ollama import Ollama


from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .

# load the environment variables
VERBOSE = (os.getenv("VERBOSE") == "True")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
USER_NAME = os.getenv("USER_NAME")
AI_NAME = os.getenv("AI_NAME")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH")



llm = Ollama(
    base_url=BASE_URL,
    verbose= VERBOSE,
    model=MODEL,
    system=SYSTEM_PROMPT,
    )

context = []
while True:
    response = llm.generateWithMemory(input(">> "))
    print("\nreceived: \n" + response)
    print("CONTEXT: \n" + str(len(llm.context)))
    


