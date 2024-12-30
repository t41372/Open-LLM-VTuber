from typing import Type
from .llm_interface import LLMInterface
from .ollama_llm import LLM as OllamaLLM
from .memgpt import LLM as MemGPTLLM
from .fake_llm import LLM as FakeLLM
from .claude_llm import LLM as ClaudeLLM


class LLMFactory:
    @staticmethod
    def create_llm(llm_provider, **kwargs) -> Type[LLMInterface]:

        if llm_provider == "ollama_llm":
            return OllamaLLM(
                system=kwargs.get("system_prompt"),
                base_url=kwargs.get("base_url"),
                model=kwargs.get("model"),
                llm_api_key=kwargs.get("llm_api_key"),
                project_id=kwargs.get("project_id"),
                organization_id=kwargs.get("organization_id"),
                verbose=kwargs.get("verbose", False),
            )
        elif llm_provider == "llama_cpp_llm":
            from .llama_cpp_llm import LLM as LlamaLLM
            return LlamaLLM(
                model_path=kwargs.get("model_path"),
                system=kwargs.get("system_prompt"),
                verbose=kwargs.get("verbose", False),
            )
        elif llm_provider == "mem0":
            from open_llm_vtuber.llm.mem0 import LLM as Mem0LLM
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
        elif llm_provider == "memgpt":
            return MemGPTLLM(
                base_url=kwargs.get("base_url"),
                server_admin_token=kwargs.get("admin_token"),
                agent_id=kwargs.get("agent_id"),
                verbose=kwargs.get("verbose", False),
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
