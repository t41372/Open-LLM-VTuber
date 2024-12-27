""" Description: This file contains the implementation of the LLM class using llama.cpp.
This class is responsible for handling the interaction with the llama.cpp for 
language generation.
"""

from typing import Iterator
import json
from llama_cpp import Llama

from .llm_interface import LLMInterface


class LLM(LLMInterface):

    def __init__(
        self,
        model_path: str,
        system: str,
        verbose: bool = False,
        **kwargs,
    ):
        """
        Initializes an instance of the LLM class using llama.cpp.

        Parameters:
        - model_path (str): Path to the GGUF model file
        - system (str): The system prompt
        - verbose (bool, optional): Enable verbose mode. Defaults to False
        - **kwargs: Additional arguments passed to Llama constructor
        """
        self.model_path = model_path
        self.system = system
        self.memory = []
        self.verbose = verbose
        self.llm = Llama(model_path=model_path, **kwargs)

        self.__set_system(system)

        if self.verbose:
            self.__printDebugInfo()

    def __set_system(self, system):
        """
        Set the system prompt
        system: str
            the system prompt
        """
        self.system = system
        self.memory.append(
            {
                "role": "system",
                "content": system,
            }
        )

    def __print_memory(self):
        """
        Print the memory
        """
        print("Memory:\n========\n")
        # for message in self.memory:
        print(self.memory)
        print("\n========\n")

    def __printDebugInfo(self):
        print(" -- Model Path: " + self.model_path)
        print(" -- System: " + self.system)

    def chat_iter(self, prompt: str) -> Iterator[str]:
        self.memory.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        if self.verbose:
            self.__print_memory()
            print(f" -- Model Path: {self.model_path}")
            print(f" -- System: {self.system}")
            print(f" -- Prompt: {prompt}\n\n")

        try:
            chat_completion = self.llm.create_chat_completion(
                messages=self.memory, stream=True
            )
        except Exception as e:
            print(f"Error calling llama.cpp: {str(e)}")
            self.__printDebugInfo()
            return iter([f"Error calling llama.cpp: {str(e)}"])

        def _generate_response():
            for chunk in chat_completion:
                try:
                    if chunk.get("choices") and chunk["choices"][0].get("delta"):
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    continue

            # Store complete response after generation
            complete_response = "".join(content for content in _generate_response())
            self.memory.append({"role": "assistant", "content": complete_response})

            with open("mem.json", "w", encoding="utf-8") as file:
                json.dump(self.memory, file)

        return _generate_response()

    def handle_interrupt(self, heard_response: str) -> None:
        if self.memory[-1]["role"] == "assistant":
            self.memory[-1]["content"] = heard_response + "..."
        else:
            if heard_response:
                self.memory.append(
                    {
                        "role": "assistant",
                        "content": heard_response + "...",
                    }
                )
        self.memory.append(
            {
                "role": "system",
                "content": "[Interrupted by user]",
            }
        )


def test():
    llm = LLM(
        model_path="/Users/tim/Desktop/gguf/qwen2.5-3b-instruct-q4_k_m.gguf",
        system='You are a sarcastic AI chatbot who loves to say "Get out and touch some grass"',
        verbose=True,
    )
    while True:
        print("\n>> (Press Ctrl+C to exit.)")
        chat_complet = llm.chat_iter(input(">> "))

        for chunk in chat_complet:
            if chunk:
                print(chunk, end="")


if __name__ == "__main__":
    test()
