from typing import AsyncIterator, List, Dict, Any, Callable
from loguru import logger

from ..sentence_divider import SentenceDivider
from .agent_interface import AgentInterface
from ..output_types import SentenceOutput, Actions
from ..stateless_llm.stateless_llm_interface import StatelessLLMInterface
from ...chat_history_manager import get_history
from ..transformers import sentence_divider, action_extractor, tts_filter, display_processor

class BasicMemoryAgent(AgentInterface):
    """
    Agent with basic chat memory using a list to store messages.
    Implements text-based responses with sentence processing pipeline.
    """

    _system: str = """You are an error message repeater. 
        Your job is repeating this error message: 
        'No system prompt set. Please set a system prompt'. 
        Don't say anything else.
        """

    def __init__(
        self,
        llm: StatelessLLMInterface,
        system: str,
        live2d_model,
        faster_first_response: bool = True,
        segment_method: str = "pysbd",
    ):
        """
        Initialize the agent with LLM, system prompt and configuration
        
        Args:
            llm: StatelessLLMInterface - The LLM to use
            system: str - System prompt
            live2d_model: Live2dModel - Model for expression extraction
            faster_first_response: bool - Whether to enable faster first response
            segment_method: str - Method for sentence segmentation
        """
        super().__init__()
        self._memory = []
        self._live2d_model = live2d_model
        self._set_llm(llm)
        self.set_system(system)
        logger.info("BasicMemoryAgent initialized.")

    def _set_llm(self, llm: StatelessLLMInterface):
        """
        Set the (stateless) LLM to be used for chat completion
        llm: StatelessLLMInterface
            the LLM
        """
        self._llm: StatelessLLMInterface = llm
        self.chat = self._chat_function_factory(llm.chat_completion)

    def set_system(self, system: str):
        """
        Set the system prompt
        system: str
            the system prompt
        """
        logger.debug(f"Memory Agent: Setting system prompt: '''{system}'''")
        self._system = system

    def _add_message(self, message: str, role: str):
        """
        Add a message to the memory
        message: str
            the message
        role: str
            the role of the message. Can be "user", "assistant", or "system"
        """
        self._memory.append(
            {
                "role": role,
                "content": message,
            }
        )

    def set_memory_from_history(self, conf_uid: str, history_uid: str) -> None:
        """Load the memory from chat history"""
        messages = get_history(conf_uid, history_uid)

        self._memory = []
        self._memory.append(
            {
                "role": "system",
                "content": self._system,
            }
        )

        for msg in messages:
            self._memory.append(
                {
                    "role": "user" if msg["role"] == "human" else "assistant",
                    "content": msg["content"],
                }
            )

    def handle_interrupt(self, heard_response: str) -> None:
        """
        Handle an interruption by the user.

        heard_response: str
            the part of the AI response heard by the user before interruption
        """
        if self._memory[-1]["role"] == "assistant":
            self._memory[-1]["content"] = heard_response + "..."
        else:
            if heard_response:
                self._memory.append(
                    {
                        "role": "assistant",
                        "content": heard_response + "...",
                    }
                )
        self._memory.append(
            {
                "role": "system",
                "content": "[Interrupted by user]",
            }
        )

    def _chat_function_factory(
        self, chat_func: Callable[[List[Dict[str, Any]], str], AsyncIterator[str]]
    ) -> Callable[..., AsyncIterator[SentenceOutput]]:
        """
        Create the chat pipeline with transformers
        
        The pipeline:
        LLM tokens -> sentence_divider -> action_extractor -> tts_filter -> display_processor
        """

        @display_processor()
        @tts_filter()
        @action_extractor(self._live2d_model)
        @sentence_divider()
        async def chat_with_memory(prompt: str) -> AsyncIterator[str]:
            """
            Chat implementation with memory and processing pipeline
            
            Args:
                prompt: str - User input
                
            Returns:
                AsyncIterator[str] - Token stream from LLM
            """
            self._add_message(prompt, "user")
            logger.debug(f"Memory Agent: Sending: '''{self._memory}'''")

            # Get token stream from LLM
            token_stream = chat_func(self._memory, self._system)
            complete_response = ""

            async for token in token_stream:
                yield token
                complete_response += token

            # Store complete response
            self._add_message(complete_response, "assistant")

        return chat_with_memory

    async def chat(self, prompt: str) -> AsyncIterator[SentenceOutput]:
        """Placeholder chat method that will be replaced at runtime"""
        return self.chat(prompt)
