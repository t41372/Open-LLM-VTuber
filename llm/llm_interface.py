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
        pass


    
    

