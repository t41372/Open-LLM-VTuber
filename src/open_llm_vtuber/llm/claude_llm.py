import anthropic
from typing import Iterator
from .llm_interface import LLMInterface

class LLM(LLMInterface):
    def __init__(
        self,
        system: str = None,
        base_url: str = None,
        model: str = "claude-3-haiku-20240307",
        llm_api_key: str = None,
        verbose: bool = False,
    ):
        """
        Initialize Claude LLM.
        
        Args:
            system (str): System prompt
            base_url (str): Base URL for Claude API
            model (str): Model name
            llm_api_key (str): Claude API key
            verbose (bool): Whether to print debug info
        """
        self.system = system
        self.model = model
        self.verbose = verbose
        
        # Initialize Claude client
        self.client = anthropic.Anthropic(
            api_key=llm_api_key,
            base_url=base_url if base_url else None
        )
        
        # Store conversation history (excluding system prompt)
        self.messages = []

    def chat_iter(self, prompt: str) -> Iterator[str]:
        """
        Send message to Claude and yield response tokens.
        
        Args:
            prompt (str): User message
            
        Yields:
            str: Response tokens
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": prompt})
        
        try:
            # Stream response from Claude
            with self.client.messages.stream(
                messages=self.messages,
                system=self.system if self.system else "",
                model=self.model,
                max_tokens=1024
            ) as stream:
                response_text = ""
                for text in stream.text_stream:
                    response_text += text
                    yield text
                
                # Add assistant response to history
                self.messages.append({
                    "role": "assistant", 
                    "content": response_text
                })
                
        except Exception as e:
            if self.verbose:
                print(f"Error in Claude chat: {str(e)}")
            yield f"Error occurred: {str(e)}"

    def handle_interrupt(self, heard_response: str) -> None:
        """
        Handle interruption by updating the last assistant message.
        
        Args:
            heard_response (str): The heard portion of the response
        """
        if self.messages and self.messages[-1]["role"] == "assistant":
            # Update last assistant message with only heard portion
            self.messages[-1]["content"] = heard_response
