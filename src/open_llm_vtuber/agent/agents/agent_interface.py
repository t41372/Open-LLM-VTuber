from enum import Enum
from abc import ABC, abstractmethod
from typing import AsyncIterator, Union, Tuple
from loguru import logger


class AgentOutputType(Enum):
    """Agent output type enumeration"""

    RAW_LLM = "raw_llm"
    TEXT_FOR_TTS = "text_tts"
    AUDIO_TEXT = "audio_text"


class AgentInterface(ABC):
    """Base interface for all agent implementations"""

    @property
    @abstractmethod
    def output_type(self) -> AgentOutputType:
        """Return the output type of this agent"""
        pass

    @abstractmethod
    async def chat(
        self, prompt: str
    ) -> Union[AsyncIterator[str], AsyncIterator[str], AsyncIterator[Tuple[str, str]]]:
        """
        Chat with the agent asynchronously.

        This function should be implemented by the agent.
        Output type depends on the agent's output_type:
        - RAW_LLM: AsyncIterator[str] - Raw LLM output stream
        - TEXT_FOR_TTS: AsyncIterator[str] - Text ready for TTS
        - AUDIO_TEXT: AsyncIterator[Tuple[str, str]] - (audio_file_path, text) pairs

        Args:
            prompt: str - User input transcription

        Returns:
            Response stream according to the agent's output_type
        """
        logger.critical("Agent: No chat function set.")
        raise ValueError("Agent: No chat function set.")

    @abstractmethod
    def handle_interrupt(self, heard_response: str) -> None:
        """
        Handle user interruption. This function will be called when the agent is interrupted by the user.

        heard_response: str
            the part of the agent's response heard by the user before interruption
        """
        logger.warning(
            """Agent: No interrupt handler set. The agent may not handle interruptions.
            correctly. The AI may not be able to understand that it was interrupted."""
        )
        pass

    @abstractmethod
    def set_memory_from_history(self, conf_uid: str, history_uid: str) -> None:
        """Load the agent's working memory from chat history"""
        pass
