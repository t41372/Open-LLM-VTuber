'''
the llm code
- runs the llm
- runs the memory
- runs the conversation
- maintain long term memory
2023-11-23
'''

from langchain.llms import Ollama
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from langchain.memory import ConversationSummaryBufferMemory

from dotenv import load_dotenv
import os
import utils

load_dotenv()  # take environment variables from .

# load the environment variables
VERBOSE = (os.getenv("VERBOSE") == "True")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
AI_NAME = os.getenv("AI_NAME")
AI_ROLE = os.getenv("AI_ROLE")
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH")



llm = Ollama(
    base_url=BASE_URL,
    verbose= VERBOSE,
    model=MODEL,
    system=AI_ROLE,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    )





prompt = ChatPromptTemplate(
    messages=[
        # SystemMessagePromptTemplate.from_template(
        #     AI_ROLE
        # ),
        # The `variable_name` here is what must align with memory
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{text}\nAI: "),
    ]

)

# Notice that we `return_messages=True` to fit into the MessagesPlaceholder
# Notice that `"chat_history"` aligns with the MessagesPlaceholder name.
memory = ConversationSummaryBufferMemory(
    llm=llm,
    memory_key="chat_history", 
    return_messages=True, 
    max_token_limit=7500)

conversation = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=VERBOSE,
    memory=memory,
)

def talkToLLM(input_text, verbose=VERBOSE):
    '''
    talk to the llm and return the response. 
    input_text: str
        the input text

    return: str
    '''
    # validate the text
    if not utils.validate_text(input_text):
        return
    # print("Validated text: ({})".format(input_text))

    result = "Error: No result from LLM. There is a problem with the LLM function. Function talkToLLM at LLM.py"
    if(verbose):
        print("\n>> Conversation:")
        print(getShortTermMemory())
    
    result = conversation({"text": input_text})['chat_history'][-1].content.strip()
    # result = conversation.predict(text=input_text).strip()
    # print(">> mem: \n")
    # getMemory()

    # The llm sometimes returns "Me: " or "AI: " at the beginning of the response.
    # We need to remove them.
    utils.removeBadPrefix(result, ["Me:", "AI:", "Unhelpful AI:", "{}:".format(AI_NAME) ])

    return result


        

def getShortTermMemory():
    '''
    get the memory of the conversation
    return: str dict 
        the chat history dictionary. Format:
        {'text': input_text, 
        'chat_history': 
            [HumanMessage(content="content"], 
            AIMessage(content="response")]
        }
    '''
    return memory.load_memory_variables({})










