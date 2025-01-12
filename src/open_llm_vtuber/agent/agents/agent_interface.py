from abc import ABC, abstractmethod
from typing import AsyncIterator, Union, Tuple, Optional
from enum import Enum
from loguru import logger
import numpy as np
import asyncio


class AgentInputType(Enum):
    """Agent input type enumeration"""
    TEXT = "text"
    AUDIO = "audio"
    BOTH = "both"


class AgentOutputType(Enum):
    """Agent output type enumeration"""
    RAW_LLM = "raw_llm"        
    TEXT_FOR_TTS = "text_tts" 
    AUDIO_TEXT = "audio_text"      


class AgentInterface(ABC):
    """Base interface for all agent implementations"""
    
    def __init__(self):
        self._human_input_future: Optional[asyncio.Future] = None

    @property
    @abstractmethod
    def output_type(self) -> AgentOutputType:
        """Return the output type of this agent"""
        pass

    @property
    @abstractmethod
    def input_type(self) -> AgentInputType:
        """Return the input type this agent accepts"""
        pass

    @abstractmethod
    async def chat(self, prompt: Union[str, np.ndarray]) -> Union[
        AsyncIterator[str],                    
        AsyncIterator[str],                    
        AsyncIterator[Tuple[str, str]]         
    ]:
        """
        Chat with the agent asynchronously.

        This function should be implemented by the agent.
        Input format depends on the agent's input_format:
        - TEXT: str - Text prompt
        - AUDIO: np.ndarray - Audio data

        Output format depends on the agent's output_format:
        - RAW_LLM: AsyncIterator[str] - Raw LLM output stream
        - TEXT_FOR_TTS: AsyncIterator[str] - Text ready for TTS
        - AUDIO_TEXT: AsyncIterator[Tuple[str, str]] - (audio_file_path, text) pairs
        
        Args:
            prompt: Union[str, np.ndarray] - Input according to agent's input_format

        Returns:
            Response stream according to the agent's output_format
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
    def set_memory_from_history(self, messages: list) -> None:
        """Load the agent's working memory from the message history"""
        pass

    @abstractmethod
    def clear_memory(self) -> None:
        """Clear the agent's working memory"""
        pass

    # Only needed for Audio or BOTH input types. Override it in subclasses if needed.
    async def get_human_input(self, audio_input: np.ndarray) -> str:
        """
        Process audio input and return human input text.
        For agents that accept AUDIO or BOTH input types.
        Can be implemented to return immediately or wait for processing.

        Args:
            audio_input: np.ndarray - Raw audio input data

        Returns:
            str - Processed human input text
        """
        if self.input_type == AgentInputType.TEXT:
            raise NotImplementedError("TEXT-only agents don't implement get_human_input")
        return "<<AUDIO_INPUT>>"
        
        # if self._human_input_future and not self._human_input_future.done():
        #     return self._human_input_future.result()

    def set_human_input(self, text: str) -> None:
        """
        Set the human input text for the future.
        Used when the agent needs to wait for processing to complete.
        """
        if self._human_input_future and not self._human_input_future.done():
            self._human_input_future.set_result(text)
