from typing import Iterator
import json

from .llm_interface import LLMInterface

class LLM(LLMInterface):

    def __init__(self):
        """
        Initializes an instance of the `FakeLLM` class.
        """
        self.memory = []
        self.sentence_count = 1
        self.response_list = [
            """Hello [smirk]! This is fake_llm. This is sentence 1. [joy]""",
            """[joy] *Hello* This is fake_llm. This is sentence... 2.. [neutral]""",
            # "",
            "Hey there! This is fake_llm. This is sentence 4. Sentence 3 was skipped. [joy]. After this, I will repeat what you say.",
        ]

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
        print(self.memory)
        print("\n========\n")

    def __printDebugInfo(self):
        print(" -- System: " + self.system)

    def chat_iter(self, prompt: str) -> Iterator[str]:

        self.memory.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        if len(self.response_list) > 0:
            response = self.response_list.pop(0)
        else:
            response = f"Sentence {self.sentence_count}: {prompt}"
            self.sentence_count += 1


        # A generator to yield the response one character at a time
        def _generate_response():
            complete_response = ""
            for char in response:
                yield char
                complete_response += char
            
            # Store the complete response in memory
            self.memory.append(
                {
                    "role": "assistant",
                    "content": complete_response,
                }
            )

            # Serialize the memory to a file
            self.serialize_memory(self.memory, 'mem.json')

        return _generate_response()

    def handle_interrupt(self, heard_response: str) -> None:
        print(">>>> LLM believe heard response is: ", heard_response)
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

    def serialize_memory(self, memory, filename):
        """
        Serialize the memory to a file.

        Parameters:
        - memory (list): The list of memory to be serialized.
        - filename (str): The name of the file to which memory should be serialized.
        """
        with open(filename, 'w') as file:
            json.dump(memory, file)
