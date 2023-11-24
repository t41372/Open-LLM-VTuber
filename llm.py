'''
the llm code
- runs the llm
- runs the memory
- runs the conversation
- maintain long term memory
2023-11-23
'''

from langchain.chat_models import ChatOllama
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
VERBOSE = os.getenv("VERBOSE")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")

llm = ChatOllama(
    base_url=BASE_URL,
    verbose= VERBOSE,
    model=MODEL,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    )

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            "You are a nice AI girl called neuro having a conversation with a human."
        ),
        # The `variable_name` here is what must align with memory
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
)

# prompt = ChatPromptTemplate(
#     messages=[
#         SystemMessagePromptTemplate.from_template(
#             "You are a nice AI girl called neuro having a conversation with a human."
#         ),
#         # The `variable_name` here is what must align with memory
#         MessagesPlaceholder(variable_name="chat_history"),
#         HumanMessagePromptTemplate.from_template("{question}")
#     ]
# )
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

def talk(input_text, verbose=VERBOSE):
    '''
    talk to the llm and return the response. 
    input_text: str
        the input text

    return: str dict 
        the llm response dictionary. Format:
        {'question': input_text, 
        'chat_history': 
            [HumanMessage(content="content"], 
            AIMessage(content="response")]
        }
    '''
    return conversation({"question": input_text})

while True:
    print(">>>>>>>>>")
    result = (talk(input(">> ")))
    print("<<<<<<<<<<<<" + "\n\n")

    # print("++++++++++++++++++++++v")
    # print(result)
    # # 
    # print("++++++++++++++++++++++^")
    # print(result['question'] + "\n")
    # print(result['chat_history'])
    # print(type(result['chat_history']))
    # print("+++++++++++ get content vvv +++++++++++^")
    # print(result['chat_history'][1])
    # print(result['chat_history'][1].content)






