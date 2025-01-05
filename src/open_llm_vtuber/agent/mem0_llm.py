"""Description: This file contains the implementation of the `ollama` class.
This class is responsible for handling the interaction with the OpenAI API for language generation.
Compatible with all of the OpenAI Compatible endpoints, including Ollama, OpenAI, and more.
"""

from typing import Iterator
from mem0 import Memory
from openai import OpenAI
from loguru import logger
from .agents.agent_interface import AgentInterface
import json


class LLM(AgentInterface):

    def __init__(
        self,
        user_id: str,
        base_url: str,
        model: str,
        system: str,
        mem0_config: dict,
        organization_id: str = "z",
        project_id: str = "z",
        llm_api_key: str = "z",
        verbose: bool = False,
    ):
        """
        Initializes an instance of the `ollama` class.

        Parameters:
        - base_url (str): The base URL for the OpenAI API.
        - model (str): The model to be used for language generation.
        - system (str): The system to be used for language generation.
        - organization_id (str, optional): The organization ID for the OpenAI API. Defaults to an empty string.
        - project_id (str, optional): The project ID for the OpenAI API. Defaults to an empty string.
        - llm_api_key (str, optional): The API key for the OpenAI API. Defaults to an empty string.
        - verbose (bool, optional): Whether to enable verbose mode. Defaults to `False`.
        """

        self.base_url = base_url
        self.model = model
        self.system = system
        self.mem0_config = mem0_config
        self.user_id = user_id

        self.conversation_memory = []
        self.verbose = verbose
        self.client = OpenAI(
            base_url=base_url,
            organization=organization_id,
            project=project_id,
            api_key=llm_api_key,
        )

        self.system = system
        self.conversation_memory = [
            {
                "role": "system",
                "content": system,
            }
        ]

        logger.debug("Initializing Memory...")
        # Initialize Memory with the configuration
        self.mem0 = Memory.from_config(self.mem0_config)
        logger.debug("Memory Initialized...")

        # Add a memory
        # self.mem0.add("I'm visiting Paris", user_id="john")

    def chat_iter(self, prompt: str) -> Iterator[str]:

        logger.debug("All Mem:")
        logger.debug(self.mem0.get_all(user_id=self.user_id))

        # Get relevant memory

        relevant_memories_list = self.mem0.search(
            query=prompt, limit=10, user_id=self.user_id
        )
        relevant_memories = ""
        if relevant_memories_list:
            relevant_memories = "\n".join(
                mem["memory"] for mem in relevant_memories_list
            )

        if relevant_memories:
            logger.debug("Relevant memories found...")
            self.conversation_memory[0] = {
                "role": "system",
                "content": f"""{self.system}
                
                ## Relevant Memories
                Here are something you recall from the past:
                ===== Some relevant memories =====
                {relevant_memories}
                ===== end of relevant memories =====
                
                """,
            }
        else:
            logger.debug("No relevant memories found...")
            self.conversation_memory[0] = {
                "role": "system",
                "content": f"""{self.system}""",
            }

        logger.debug("System:")
        logger.debug(self.conversation_memory[0])

        self.conversation_memory.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        this_conversation_mem = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        chat_completion = []
        try:
            logger.debug("Calling the chat endpoint with...")
            logger.debug(self.conversation_memory)
            chat_completion = self.client.chat.completions.create(
                messages=self.conversation_memory,
                model=self.model,
                stream=True,
            )
        except Exception as e:
            logger.error("Error calling the chat endpoint: " + str(e))
            logger.error(self.mem0_config)
            return "Error calling the chat endpoint: " + str(e)

        # a generator to give back an iterator to the response that will store
        # the complete response in memory once the iteration is done
        def _generate_and_store_response():
            complete_response = ""
            for chunk in chat_completion:
                if chunk.choices[0].delta.content is None:
                    chunk.choices[0].delta.content = ""
                yield chunk.choices[0].delta.content
                complete_response += chunk.choices[0].delta.content

            self.conversation_memory.append(
                {
                    "role": "assistant",
                    "content": complete_response,
                }
            )

            this_conversation_mem.append(
                {
                    "role": "assistant",
                    "content": complete_response,
                }
            )

            # Add the conversation to the memory
            logger.debug(self.mem0.add(this_conversation_mem, user_id=self.user_id))

            logger.debug(f"Mem0 Added... {this_conversation_mem}")

            logger.debug("All Mem:")
            logger.debug(self.mem0.get_all(user_id=self.user_id))

            def serialize_memory(memory, filename):
                with open(filename, "w") as file:
                    json.dump(memory, file)

            serialize_memory(self.conversation_memory, "mem.json")
            return

        return _generate_and_store_response()

    def handle_interrupt(self, heard_response: str) -> None:
        if self.conversation_memory[-1]["role"] == "assistant":
            self.conversation_memory[-1]["content"] = heard_response + "..."
        else:
            if heard_response:
                self.conversation_memory.append(
                    {
                        "role": "assistant",
                        "content": heard_response + "...",
                    }
                )
        self.conversation_memory.append(
            {
                "role": "system",
                "content": "[Interrupted by user]",
            }
        )


def test():

    test_config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "test",
                "host": "localhost",
                "port": 6333,
                "embedding_model_dims": 768,  # Change this according to your local model's dimensions
            },
        },
        "llm": {
            "provider": "ollama",
            "config": {
                "model": "llama3.1:latest",
                "temperature": 0,
                "max_tokens": 8000,
                "ollama_base_url": "http://localhost:11434",  # Ensure this URL is correct
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "mxbai-embed-large:latest",
                # Alternatively, you can use "snowflake-arctic-embed:latest"
                "ollama_base_url": "http://localhost:11434",
            },
        },
    }

    llm = LLM(
        user_id="rina",
        base_url="http://localhost:11434/v1",
        model="llama3:latest",
        mem0_config=test_config,
        system='You are a sarcastic AI chatbot who loves to the jokes "Get out and touch some grass"',
        organization_id="organization_id",
        project_id="project_id",
        llm_api_key="llm_api_key",
        verbose=True,
    )
    while True:
        print("\n>> (Press Ctrl+C to exit.)")
        chat_complet = llm.chat_iter(input(">> "))

        for chunk in chat_complet:
            if chunk:
                print(chunk, end="")


if __name__ == "__main__":
    test()
