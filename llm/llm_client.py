from letta import LLMConfig, EmbeddingConfig
from letta import create_client
from letta.schemas.memory import ChatMemory

from llm.llm_interface import LLMInterface

client = create_client()
from loguru import logger


# Initialize the MemGPT instance
class LettaLLMClient(LLMInterface):

    def __init__(self):
        """
        Initializes the memGPT client with persistent memory and the specified model.

        """
        self.client = create_client()
        self.agent = None
        self.memory = None

    def initialize(self, name, persona, model):
        self.client.set_default_llm_config(LLMConfig.default_config(model))
        self.client.set_default_embedding_config(EmbeddingConfig.default_config(provider="openai"))
        self.memory = ChatMemory(human=name, persona=persona)
        self.agent = self.client.create_agent(name, memory=self.memory)

    def chat_iter(self, prompt):
        """
        Send a prompt to the memGPT agent and get the response.
        :param prompt: prompt to infer.

        :return: Response from the agent.
        """
        response = self.client.send_message(
            agent_id=self.agent.id,
            message=prompt,
            role="user"
        )
        logger.error(response.usage)
        return response.messages

    def reset_memory(self):
        """
        Clears the memory for the agent.
        """
        self.memory.clear()
