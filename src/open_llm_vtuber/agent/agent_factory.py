from typing import Type
from .agent_interface import AgentInterface
from .agents.basic_memory_agent import BasicMemoryAgent

from .stateless_llm_factory import LLMFactory
from .stateless_llm.claude_llm import LLM as ClaudeLLM

from .memgpt import LLM as MemGPTLLM
from .fake_llm import LLM as FakeLLM



class LLMFactory:
    @staticmethod
    def create_llm(conversation_agent_choice, **kwargs) -> Type[AgentInterface]:

        if conversation_agent_choice == "basic_memory_agent":
            return BasicMemoryAgent(
                llm=kwargs.get("llm")
            )
            
        elif conversation_agent_choice == "mem0":
            from open_llm_vtuber.agent.mem0_llm import LLM as Mem0LLM
            return Mem0LLM(
                user_id=kwargs.get("user_id"),
                system=kwargs.get("system_prompt"),
                base_url=kwargs.get("base_url"),
                model=kwargs.get("model"),
                llm_api_key=kwargs.get("llm_api_key"),
                project_id=kwargs.get("project_id"),
                organization_id=kwargs.get("organization_id"),
                mem0_config=kwargs.get("mem0_config"),
                verbose=kwargs.get("verbose", False)
            )
        elif conversation_agent_choice == "memgpt":
            return MemGPTLLM(
                base_url=kwargs.get("base_url"),
                server_admin_token=kwargs.get("admin_token"),
                agent_id=kwargs.get("agent_id"),
                verbose=kwargs.get("verbose", False),
            )
        elif conversation_agent_choice == "claude_llm":
            return ClaudeLLM(
                system=kwargs.get("system_prompt"),
                base_url=kwargs.get("base_url"),
                model=kwargs.get("model"),
                llm_api_key=kwargs.get("llm_api_key"),
                verbose=kwargs.get("verbose", False),
            )
        elif conversation_agent_choice == "fake_llm":
            return FakeLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {conversation_agent_choice}")


# 使用工廠創建 LLM 實例
# llm_instance = LLMFactory.create_llm("ollama", **config_dict)
