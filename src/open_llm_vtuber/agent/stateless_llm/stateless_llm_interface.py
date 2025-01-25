import abc
from typing import AsyncIterator, List, Dict, Any


class StatelessLLMInterface(metaclass=abc.ABCMeta):
    """
    Interface for a stateless language model.

    The word "stateless" means that the language model does not store memory,
    system prompts, or user messages, which is most of the LLM. If we send a
    message to the LLM, its response will be based on the message parameter alone.

    The StatelessLLMInterface class provides a method for generating chat
    completions asynchronously.

    We use StatelessLLMs to initialize Agents, which pack the StatelessLLM with
    memory, system prompts, and other features.

    """

    @abc.abstractmethod
    async def chat_completion(
        self, messages: List[Dict[str, Any]], system: str = None
    ) -> AsyncIterator[str]:
        """
        Generates a chat completion asynchronously and return an iterator to the response.
        This function does not store memory or user messages.

        Parameters:
        - messages (List[Dict[str, Any]]): The list of messages to send to the API.
        - system (str, optional): System prompt to use for this completion.

        Yields:
        - str: The content of each chunk from the API response.

        Raises:
        - APIConnectionError: When the server cannot be reached
        - RateLimitError: When a 429 status code is received
        - APIError: For other API-related errors
        """
        raise NotImplementedError
