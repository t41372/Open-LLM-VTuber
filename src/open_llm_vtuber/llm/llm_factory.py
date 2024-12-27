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
                system=kwargs.get("SYSTEM_PROMPT"),
                base_url=kwargs.get("BASE_URL"),
                model=kwargs.get("MODEL"),
                llm_api_key=kwargs.get("LLM_API_KEY"),
                project_id=kwargs.get("PROJECT_ID"),
                organization_id=kwargs.get("ORGANIZATION_ID"),
                verbose=kwargs.get("VERBOSE", False),
            )
        elif llm_provider == "llama_cpp_llm":
            from .llama_cpp_llm import LLM as LlamaLLM
            return LlamaLLM(
                model_path=kwargs.get("MODEL_PATH"),
                system=kwargs.get("SYSTEM_PROMPT"),
                verbose=kwargs.get("VERBOSE", False),
            )
        elif llm_provider == "mem0":
            from open_llm_vtuber.llm.mem0 import LLM as Mem0LLM
            return Mem0LLM(
                user_id=kwargs.get("USER_ID"),
                system=kwargs.get("SYSTEM_PROMPT"),
                base_url=kwargs.get("BASE_URL"),
                model=kwargs.get("MODEL"),
                llm_api_key=kwargs.get("LLM_API_KEY"),
                project_id=kwargs.get("PROJECT_ID"),
                organization_id=kwargs.get("ORGANIZATION_ID"),
                mem0_config=kwargs.get("MEM0_CONFIG"),
                verbose=kwargs.get("VERBOSE", False)
            )
        elif llm_provider == "memgpt":
            return MemGPTLLM(
                base_url=kwargs.get("BASE_URL"),
                server_admin_token=kwargs.get("ADMIN_TOKEN"),
                agent_id=kwargs.get("AGENT_ID"),
                verbose=kwargs.get("VERBOSE", False),
            )
        elif llm_provider == "claude_llm":
            return ClaudeLLM(
                system=kwargs.get("SYSTEM_PROMPT"),
                base_url=kwargs.get("BASE_URL"),
                model=kwargs.get("MODEL"),
                llm_api_key=kwargs.get("LLM_API_KEY"),
                verbose=kwargs.get("VERBOSE", False),
            )
        elif llm_provider == "fake_llm":
            return FakeLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")


# 使用工廠創建 LLM 實例
# llm_instance = LLMFactory.create_llm("ollama", **config_dict)
