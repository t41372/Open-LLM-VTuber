from letta import LLMConfig, EmbeddingConfig
from letta import create_client
from letta.schemas.memory import ChatMemory

from llm.llm_interface import LLMInterface
from utils.OutputQueue import OutputQueue

client = create_client()
from loguru import logger
import json


# Initialize the MemGPT instance
class LettaLLMClient(LLMInterface):

    def __init__(self):
        """
        Initializes the memGPT client with persistent memory and the specified model.

        """
        self.url = 'http://localhost:8283/'
        self.client = create_client(base_url=self.url)
        self.agent = None
        self.memory = None
        self.agent_id = None
        self.inference_message_key = 'function_call'  ## this is the key the inference message has in the LLM response
        self.memory_message_key = 'internal_monologue'  ## key for internal monologue

    def initialize(self, name, persona, model="gpt-4o-mini"):
        try:
            self.client.set_default_llm_config(LLMConfig.default_config(model_name=model))
            self.client.set_default_embedding_config(
                EmbeddingConfig.default_config(model_name="text-embedding-ada-002"))
            self.memory = ChatMemory(human='GoldRoger', persona=persona)
            self.agent_id = client.get_agent_id(agent_name=name)
            if self.agent_id is None:
                self.agent = self.client.create_agent(name=name, memory=self.memory)
                logger.success(f"CREATED AGENT {self.agent.name}")
            else:
                self.agent = self.client.get_agent(agent_id=self.agent_id)
                logger.success(f"AGENT ALREADY EXISTS, FETCHING AGENT: {self.agent.name}")
        except ValueError as e:
            logger.error(e)

    def chat_iter(self, prompt):
        """
        Send a prompt to the memGPT agent and get the response.
        :param prompt: prompt to infer.

        :return: Response from the agent.
        """
        response = self.client.user_message(
            agent_id=self.agent.id,
            message=prompt
        )
        temp_chunks = []
        for chunk in response:
            try:
                chunk_json = json.loads(chunk.json())  # Decode the chunk
                # Validate and extract desired content
                if chunk_json['message_type'] in self.inference_message_key and 'arguments' in chunk_json[
                    self.inference_message_key]:
                    temp_chunks.append(chunk_json['function_call']['arguments'])  # Collect chunk data

                    # When 5 chunks are collected, add them to the output queue
                    if len(temp_chunks) == 10:
                        combined_output = "".join(temp_chunks)  # Combine the 5 chunks
                        OutputQueue().add_output(combined_output)
                        temp_chunks = []  # Reset temporary list

            except Exception:

                continue  # Skip invalid or incomplete chunks

            # for message in response.messages:
            #     if message.message_type == self.inference_message_key:
            #         function_call_message= json.loads(message.json())['function_call']['arguments']
            #         return json.loads(function_call_message)['message']
            # return response.messages

    def reset_memory(self):
        """
        Clears the memory for the agent.
        """
        self.memory.clear()
