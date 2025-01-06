from typing import Type
from loguru import logger

#!
from .agents.agent_interface import AgentInterface

from .stateless_llm.stateless_llm_interface import StatelessLLMInterface

from .stateless_llm.openai_compatible_llm import AsyncLLM as OpenAICompatibleLLM
from .fake_llm import LLM as FakeLLM
from .stateless_llm.claude_llm import LLM as ClaudeLLM


class LLMFactory:
    @staticmethod
    def create_llm(llm_provider, **kwargs) -> Type[StatelessLLMInterface]:
        """Create an LLM based on the configuration.

        Args:
            llm_provider: The type of LLM to create
            **kwargs: Additional arguments
        """
        logger.info(f"Initializing LLM: {llm_provider}")

        if llm_provider == "openai_compatible_llm":
            return OpenAICompatibleLLM(
                model=kwargs.get("model"),
                base_url=kwargs.get("base_url"),
                llm_api_key=kwargs.get("llm_api_key"),
                organization_id=kwargs.get("organization_id"),
                project_id=kwargs.get("project_id"),
            )
        elif llm_provider == "llama_cpp_llm":
            from .stateless_llm.llama_cpp_llm import LLM as LlamaLLM

            return LlamaLLM(
                model_path=kwargs.get("model_path"),
            )
        elif llm_provider == "claude_llm":
            return ClaudeLLM(
                system=kwargs.get("system_prompt"),
                base_url=kwargs.get("base_url"),
                model=kwargs.get("model"),
                llm_api_key=kwargs.get("llm_api_key"),
                verbose=kwargs.get("verbose", False),
            )
        elif llm_provider == "fake_llm":
            return FakeLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")


# 使用工廠創建 LLM 實例
# llm_instance = LLMFactory.create_llm("ollama", **config_dict)
