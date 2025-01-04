from typing import AsyncIterator, List, Dict, Any, Callable


class BasicMemory:
    """
    Basic Chat Memory implementation.
    This class provides a simple memory based on list for chat agents to store messages.
    """

    def __init__(self):
        self.memory = []
        self.system: str = """You are an error message repeater. 
        Your job is repeating this error message: 
        'No system prompt set. Please set a system prompt'. 
        Don't say anything else.
        """

    def set_system(self, system: str):
        """
        Set the system prompt
        system: str
            the system prompt
        """
        self.system = system

    def add_message(self, message: str, role: str):
        """
        Add a message to the memory
        message: str
            the message
        role: str
            the role of the message. Can be "user", "assistant", or "system"
        """
        self.memory.append(
            {
                "role": role,
                "content": message,
            }
        )

    def chat_with_memory_decor(
        self, chat_func: Callable[[List[Dict[str, Any]]], AsyncIterator[str]]
    ) -> Callable[[str], AsyncIterator[str]]:
        """
        Decorator for async chat functions that need memory.

        Parameters:
        -----------
        chat_func : ChatCompletionFunc
            The async chat completion function to wrap. Must take a list of message
            dictionaries and return an AsyncIterator[str].

        Returns:
        --------
        Callable[[str], AsyncIterator[str]]
            An async function that takes a prompt string and returns an AsyncIterator of
            response chunks.
        """

        async def chat_with_memory(prompt: str) -> AsyncIterator[str]:
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": self.system},
                *self.memory,
                {"role": "user", "content": prompt},
            ]

            # Add user message to memory first
            self.add_message(prompt, "user")

            # Create response accumulator
            full_response = []

            # Get the async iterator from chat_func
            async for chunk in chat_func(messages):
                full_response.append(chunk)
                yield chunk

            # Add the complete response to memory
            complete_response = "".join(full_response)
            self.add_message(complete_response, "assistant")

        return chat_with_memory
