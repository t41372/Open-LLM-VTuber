from typing import AsyncIterator, List, Dict, Any, Callable

from loguru import logger

from ..sentence_divider import SentenceDivider
from .agent_interface import AgentInterface, AgentOutputType
from ..stateless_llm.stateless_llm_interface import StatelessLLMInterface
from ...chat_history_manager import get_history


class BasicMemoryAgent(AgentInterface):
    """
    Agent with the most Basic Chat Memory.
    This class provides a simple memory based on list for chat agents to store messages.
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
        faster_first_response: bool = True,
        segment_method: str = "pysbd",
    ):
        super().__init__()
        self.sentence_divider = SentenceDivider(
            faster_first_response=faster_first_response, segment_method=segment_method
        )
        self._memory = []
        self._set_llm(llm)
        self.set_system(system)
        logger.info("BasicMemoryAgent initialized.")

    # chat function will be set by set_llm.
    # The default chat function (which handles error when not override) is in
    # the base class.

    # ============== Setter ==============

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
    ) -> Callable[[str], AsyncIterator[str]]:
        """
        A factory to build async chat functions that uses memory and splits
        responses into sentences.
        """

        async def chat_with_memory(prompt: str) -> AsyncIterator[str]:
            """
            Sends a user prompt (asynchronously) to the chat function
            and returns an iterator to the response sentences.

            This method is stateful and stores messages in the conversation
            memory.

            Parameters:
                prompt : str
                    The user prompt to send to the chat function.

            Yields:
                str
                    A chunk of the response from the chat function.
            """
            self._add_message(prompt, "user")
            logger.critical(f"Memory Agent: Sending: '''{self._memory}'''")

            # Reset sentence divider state
            self.sentence_divider.reset()

            # Process the response stream
            token_stream = chat_func(self._memory, self._system)
            complete_response = ""

            async for sentence in self.sentence_divider.process_stream(token_stream):
                yield sentence
                complete_response = sentence

            # Add the complete response to memory
            self._add_message(complete_response, "assistant")

        return chat_with_memory

    @property
    def output_type(self) -> AgentOutputType:
        """Return the output type of this agent"""
        return AgentOutputType.TEXT

    async def chat(self, prompt: str) -> AsyncIterator[str]:
        """Placeholder for the chat method that will be replaced at runtime"""
        return self.chat(prompt)
