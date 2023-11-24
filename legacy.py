from langchain.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationSummaryBufferMemory


print("\n>> Loading LLM...\n")

ollama = Ollama(
    base_url="http://localhost:11434",
    verbose=True,
    model="mistral-openorca:latest", 
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
)

memory = ConversationSummaryBufferMemory(llm=ollama, max_token_limit=8000)

# memory.save_context({"input": "hi"}, {"output": "whats up"})
# memory.save_context({"input": "not much. just feeling like a horse wanting to throw his llm in to the garbage bin"}, {"output": "ok"})
# print(memory.load_memory_variables({}))



def talk(text, local_memory):

    # conversation = LLMChain(
    #     llm=ollama,
    #     prompt=PromptTemplate.from_template(template),
    #     memory=local_memory,
    #     callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    # )

    local_memory.chat_memory.add_user_message(text)
    response = ollama(text, memory=local_memory)
    local_memory.chat_memory.add_ai_message(response)

    return response

while True:
    print(talk(text=input(">> "), local_memory=memory))
    print("\n\n")
    print(memory.load_memory_variables({}))
    







