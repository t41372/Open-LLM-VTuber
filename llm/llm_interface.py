import abc
from typing import Iterator


class LLMInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def chat_iter(self, prompt: str) -> Iterator[str]:
        """
        Sends a chat prompt to an agent and return an iterator to the response.
        This function will have to store the user message and ai response back to the memory.

        Parameters:
        - prompt (str): The message or question to send to the agent.

        Returns:
        - Iterator[str]: An iterator to the response from the agent.
        """
        raise NotImplementedError

    def handle_interrupt(self, heard_response: str) -> None:
        """
        This function will be called when the LLM is interrupted by the user.
        The function needs to let the LLM know that it was interrupted and let it know that the user only heard the content in the heard_response.
        The function should either (consider that some LLM provider may not support editing past memory):
        - Update the LLM's memory (to only keep the heard_response instead of the full response generated) and let it know that it was interrupted at that point.
        - Signal the LLM about the interruption.

        Parameters:
        - heard_response (str): The last response from the LLM before it was interrupted. The only content that the user can hear before the interruption.
        """
        raise NotImplementedError
