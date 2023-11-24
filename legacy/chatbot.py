from langchain.chat_models import ChatOllama
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .

# load the environment variables
VERBOSE = os.getenv("VERBOSE")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
AI_ROLE = "You are an unhelpful and sarcastic AI that makes fun of humans. You are having a conversation with a human."

# LLM
llm = ChatOllama(
    base_url=BASE_URL,
    verbose= VERBOSE,
    model=MODEL,
    )

# Prompt
# prompt = ChatPromptTemplate(
#     messages=[
#         SystemMessagePromptTemplate.from_template(
#             # "You are a nice chatbot having a conversation with a human."
#             AI_ROLE
#         ),
#         # The `variable_name` here is what must align with memory
#         MessagesPlaceholder(variable_name="chat_history"),
#         HumanMessagePromptTemplate.from_template("{question}"),
#     ]
# )


prompt = PromptTemplate(
    input_variables=["chat_history", "human_input"], 
    template=
    """AI is an unhelpful and sarcastic AI that makes fun of Human.

    {chat_history}
    Human: {human_input}
    AI:"""
)

# Notice that we `return_messages=True` to fit into the MessagesPlaceholder
# Notice that `"chat_history"` aligns with the MessagesPlaceholder name
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=500, memory_key="chat_history", return_messages=True)
conversation = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)



# Notice that we just pass in the `question` variables - `chat_history` gets populated by memory
# while True:
output = conversation.predict(human_input="Hello! Can I have an apple?")
print(output)

