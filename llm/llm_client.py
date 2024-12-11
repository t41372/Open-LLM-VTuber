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

    def initialize(self, name, persona, model="gpt-4o-mini"):
        try:
            self.client.set_default_llm_config(LLMConfig.default_config(model_name=model))
            self.client.set_default_embedding_config(
                EmbeddingConfig.default_config(model_name="text-embedding-ada-002"))
            self.memory = ChatMemory(human='GoldRoger', persona=persona)
            self.agent = self.client.create_agent(name=name,memory=self.memory)
            self.client.get_agent_by_name()
            logger.success(f"CREATED AGENT {self.agent.name}")
        except ValueError as e:
            logger.success(f"AGENT ALREADY EXISTS, FETCHING AGENT: {e}")
            self.agent = client.get_agent_by_name(name)

    def chat_iter(self, prompt):
        """
        Send a prompt to the memGPT agent and get the response.
        :param prompt: prompt to infer.

        :return: Response from the agent.
        """
        try:
            response = self.client.send_message(
                agent_id=self.agent.id,
                message=prompt,
                role="agent"
            )
            logger.error(response.usage)
            return response.messages
        except Exception as e:
            logger.error(e)

    def reset_memory(self):
        """
        Clears the memory for the agent.
        """
        self.memory.clear()
