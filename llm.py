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

load_dotenv()  # take environment variables from .

# load the environment variables
VERBOSE = (os.getenv("VERBOSE") == "True")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
AI_ROLE = "You are an unhelpful and sarcastic AI that makes fun of humans. You are having a conversation with a human."

llm = Ollama(
    base_url=BASE_URL,
    verbose= VERBOSE,
    model=MODEL,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    )

# prompt = ChatPromptTemplate(
#     messages=[
#         SystemMessage( content=
#             "You are a sarcastic AI girl called neuro having a conversation with a human."
#         ),
#         # The `variable_name` here is what must align with memory
#         MessagesPlaceholder(variable_name="chat_history"),
#         HumanMessage(content = "{text}")
#     ]
# )

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            AI_ROLE
        ),
        # The `variable_name` here is what must align with memory
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{text}")
    ]
)

# Notice that we `return_messages=True` to fit into the MessagesPlaceholder
# Notice that `"chat_history"` aligns with the MessagesPlaceholder name.
memory = ConversationSummaryBufferMemory(
    llm=llm,
    memory_key="chat_history", 
    return_messages=True, 
    max_token_limit=8000)

conversation = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=VERBOSE,
    memory=memory
)

def talkToLLM(input_text, verbose=VERBOSE):
    '''
    talk to the llm and return the response. 
    input_text: str
        the input text

    return: str
    '''
    result = "Error: No result from LLM. There is a problem with the LLM function. Function talkToLLM at LLM.py"
    if(verbose):
        print("\n>> Conversation:")
        print(conversation({"text": input_text}) )
    
    result = conversation({"text": input_text})['chat_history'][-1].content
    # The llm sometimes returns "Me: " or "AI: " at the beginning of the response.
    # We need to remove them.
    if result.startswith("Me:"):
        result = result[4:]
    elif result.startswith("AI:"):
        result = result[4:]
        
    return result


        

def getMemory():
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




# while True:
#     print(">>>>>>>>>")
#     result = talk(input(">> "))
#     print("<<<<<<<<<<<<" + "\n\n")

#     # print("++++++++++++++++++++++v")
#     # print(result)
#     # # 
#     # print("++++++++++++++++++++++^")
#     # print(result['text'] + "\n")
#     # print(result['chat_history'])
#     # print(type(result['chat_history']))
#     # print("+++++++++++ get content vvv +++++++++++^")
#     # print(result['chat_history'][1])
#     # print(result['chat_history'][1].content)






