from abc import ABC, abstractmethod
from typing import AsyncIterator
from loguru import logger


class AgentInterface(ABC):
    """Base interface for all agent implementations"""

    async def chat(self, prompt: str) -> AsyncIterator[str]:
        """
        Chat with the agent.
        prompt: str
            the prompt

        Returns:
        AsyncIterator[str]: An iterator to the response
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
