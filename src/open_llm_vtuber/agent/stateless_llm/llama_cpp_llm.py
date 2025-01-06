"""Description: This file contains the implementation of the LLM class using llama.cpp.
This class provides a stateless interface to llama.cpp for language generation.
"""

from typing import AsyncIterator, List, Dict, Any
import asyncio
from llama_cpp import Llama
from loguru import logger

from .stateless_llm_interface import StatelessLLMInterface


class LLM(StatelessLLMInterface):
    def __init__(
        self,
        model_path: str,
        **kwargs,
    ):
        """
        Initializes a stateless instance of the LLM class using llama.cpp.

        Parameters:
        - model_path (str): Path to the GGUF model file
        - **kwargs: Additional arguments passed to Llama constructor
        """
        logger.info(f"Initializing llama cpp with model path: {model_path}")
        self.model_path = model_path
        try:
            self.llm = Llama(model_path=model_path, **kwargs)
        except Exception as e:
            logger.critical(f"Failed to initialize Llama model: {e}")
            raise

    async def chat_completion(
        self, messages: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """
        Generates a chat completion using llama.cpp asynchronously.

        Parameters:
        - messages (List[Dict[str, Any]]): The list of messages to send to the model.

        Yields:
        - str: The content of each chunk from the model response.
        """
        logger.debug(f"Generating completion for messages: {messages}")

        try:
            # Create chat completion in a separate thread to avoid blocking
            chat_completion = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.llm.create_chat_completion(
                    messages=messages,
                    stream=True,
                ),
            )

            # Process chunks
            for chunk in chat_completion:
                if chunk.get("choices") and chunk["choices"][0].get("delta"):
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
