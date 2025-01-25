"""Description: This file contains the implementation of the `AsyncLLM` class for Claude API.
This class is responsible for handling asynchronous interaction with Claude API endpoints
for language generation.
"""

from typing import AsyncIterator, List, Dict, Any
from anthropic import AsyncAnthropic, AsyncStream
from loguru import logger

from .stateless_llm_interface import StatelessLLMInterface


class AsyncLLM(StatelessLLMInterface):
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        base_url: str = None,
        llm_api_key: str = None,
        system: str = None,
    ):
        """
        Initialize Claude LLM.

        Args:
            model (str): Model name
            base_url (str): Base URL for Claude API
            llm_api_key (str): Claude API key
            system (str): System prompt
        """
        self.model = model
        self.system = system

        # Initialize Claude client
        self.client = AsyncAnthropic(
            api_key=llm_api_key, base_url=base_url if base_url else None
        )

        logger.info(f"Initialized Claude AsyncLLM with model: {self.model}")
        logger.debug(f"Base URL: {base_url}")

    async def chat_completion(
        self, messages: List[Dict[str, Any]], system: str = None
    ) -> AsyncIterator[str]:
        """
        Generates a chat completion using the Claude API asynchronously.

        Parameters:
        - messages (List[Dict[str, Any]]): The list of messages to send to the API.
        - system (str, optional): System prompt to use for this completion.

        Yields:
        - str: The content of each chunk from the API response.
        """
        try:
            # Filter out system messages from the conversation as Claude doesn't support them in messages
            filtered_messages = [msg for msg in messages if msg["role"] != "system"]

            logger.debug(f"Sending messages to Claude API: {filtered_messages}")
            stream: AsyncStream = await self.client.messages.create(
                messages=filtered_messages,
                system=system if system else (self.system if self.system else ""),
                model=self.model,
                max_tokens=1024,
                stream=True,
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    if chunk.delta.text is None:
                        chunk.delta.text = ""
                    yield chunk.delta.text

        except Exception as e:
            logger.error(f"Claude API error occurred: {str(e)}")
            logger.info(f"Model: {self.model}")
            raise

        finally:
            logger.debug("Chat completion done.")
            await stream.close()
            logger.debug("Closed Claude API client.")
