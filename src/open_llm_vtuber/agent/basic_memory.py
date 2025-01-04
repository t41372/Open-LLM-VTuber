from typing import Iterator, List, Dict, Any
from loguru import logger


class BasicMemory:
    """Basic Chat Memory implementation"""

    def __init__(self):
        self.memory = []
        self.system: str = """You are an error message repeater. 
        Your job is repeating this error message: 
        'No system prompt set. Please set a system prompt'. 
        Don't say anything else.
        """

    def set_system(self, system):
        """
        Set the system prompt
        system: str
            the system prompt
        """
        self.system = system

    def add_message(self, message, role):
        """
        Add a message to the memory
        message: str
            the message
        role: str
            the role of the message
        """
        self.memory.append(
            {
                "role": role,
                "content": message,
            }
        )

    def chat_with_memory_decor(self, chat_func):
        """
        Decorator for chat functions that need memory.
        "You Want Memory? We've Got Your Back!"
        chat_func: function
            the chat function
        """

        def chat_with_memory(prompt: str) -> Iterator[str]:
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": self.system},
                *self.memory,
                {"role": "user", "content": prompt},
            ]

            # Add user message to memory first
            self.add_message(prompt, "user")
            
            # Create response accumulator
            full_response = []
            
            # Get the iterator from chat_func
            response_iterator = chat_func(messages)
            
            # Yield responses while accumulating them
            for chunk in response_iterator:
                full_response.append(chunk)
                yield chunk
                
            # Add the complete response to memory
            complete_response = "".join(full_response)
            self.add_message(complete_response, "assistant")

        return chat_with_memory
