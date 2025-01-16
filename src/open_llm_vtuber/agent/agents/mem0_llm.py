"""Description: Memory-enhanced LLM agent implementation using mem0."""

from typing import Iterator, AsyncIterator
import json
from openai import OpenAI
from loguru import logger
from mem0 import Memory

from .agent_interface import AgentInterface, AgentOutputType
from ...chat_history_manager import get_history

class LLM(AgentInterface):
    def __init__(
        self,
        user_id: str,
        base_url: str,
        model: str,
        system: str,
        mem0_config: dict,
        organization_id: str = "",
        project_id: str = "",
        llm_api_key: str = "",
        verbose: bool = False,
    ):
        super().__init__()
        self.base_url = base_url
        self.model = model
        self.system = system
        self.mem0_config = mem0_config
        self.user_id = user_id
        self.verbose = verbose
        
        self.client = OpenAI(
            base_url=base_url,
            organization=organization_id,
            project=project_id,
            api_key=llm_api_key,
        )

        self.conversation_memory = [
            {
                "role": "system",
                "content": system,
            }
        ]

        logger.debug("Initializing Memory...")
        self.mem0 = Memory.from_config(self.mem0_config)
        logger.debug("Memory Initialized...")

    @property 
    def output_type(self) -> AgentOutputType:
        return AgentOutputType.RAW_LLM

    async def chat(self, prompt: str) -> AsyncIterator[str]:
        """Async wrapper for chat_iter"""
        for token in self.chat_iter(prompt):
            yield token

    def set_memory_from_history(self, conf_uid: str, history_uid: str) -> None:
        """Load agent memory from chat history"""
        messages = get_history(conf_uid, history_uid)
        
        # Keep system message
        system_message = next(
            (msg for msg in self.conversation_memory if msg["role"] == "system"), None
        )
        self.conversation_memory = []
        if system_message:
            self.conversation_memory.append(system_message)

        # Add history messages
        for msg in messages:
            self.conversation_memory.append({
                "role": "user" if msg["role"] == "human" else "assistant",
                "content": msg["content"]
            })
            
            # Also add to mem0
            self.mem0.add([{
                "role": "user" if msg["role"] == "human" else "assistant",
                "content": msg["content"]
            }], user_id=self.user_id)

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
