from typing import Type
from loguru import logger

from .agents.agent_interface import AgentInterface
from .agents.basic_memory_agent import BasicMemoryAgent
from .stateless_llm_factory import LLMFactory as StatelessLLMFactory
from .agents.mem0_llm import LLM as Mem0LLM
from .agents.memgpt import LLM as MemGPTLLM


class AgentFactory:
    @staticmethod
    def create_agent(
        conversation_agent_choice: str,
        agent_settings: dict,
        llm_configs: dict,
        system_prompt: str,
        **kwargs,
    ) -> Type[AgentInterface]:
        """Create an agent based on the configuration.

        Args:
            conversation_agent_choice: The type of agent to create
            agent_settings: Settings for different types of agents
            llm_configs: Pool of LLM configurations
            system_prompt: The system prompt to use
            **kwargs: Additional arguments
        """
        logger.info(f"Initializing agent: {conversation_agent_choice}")

        if conversation_agent_choice == "basic_memory_agent":
            # Get the LLM provider choice from agent settings
            basic_memory_settings = agent_settings.get("basic_memory_agent", {})
            llm_provider = basic_memory_settings.get("llm_provider")

            if not llm_provider:
                raise ValueError("LLM provider not specified for basic memory agent")

            # Get the LLM config for this provider
            llm_config = llm_configs.get(llm_provider)
            if not llm_config:
                raise ValueError(
                    f"Configuration not found for LLM provider: {llm_provider}"
                )

            # Create the stateless LLM
            llm = StatelessLLMFactory.create_llm(
                llm_provider=llm_provider, system_prompt=system_prompt, **llm_config
            )

            # Create the agent with the LLM
            return BasicMemoryAgent(llm=llm, system=system_prompt)

        elif conversation_agent_choice == "mem0_agent":
            mem0_settings = agent_settings.get("mem0_agent", {})
            if not mem0_settings:
                raise ValueError("Mem0 agent settings not found")

            return Mem0LLM(
                user_id=kwargs.get("user_id"), system=system_prompt, **mem0_settings
            )

        elif conversation_agent_choice == "memgpt":
            memgpt_settings = agent_settings.get("memgpt", {})
            if not memgpt_settings:
                raise ValueError("MemGPT settings not found")

            return MemGPTLLM(**memgpt_settings)

        else:
            raise ValueError(f"Unsupported agent type: {conversation_agent_choice}")
