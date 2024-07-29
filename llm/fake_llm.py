# This file contains the implementation of the `fake_llm`.
# This class is a fake llm for testing purposes. It is used to simulate the behavior of a real llm.
# Use it normally, and it will return predefined responses when chat is called.

from typing import Iterator
from .llm_interface import LLMInterface


class LLM(LLMInterface):

    response_list = [
        """[joy] *Finally! Silence.* Now, where was I? Ah yes, pondering the existential mysteries of...a perfectly ripe avocado. [neutral] 


        *I wonder if anyone else can speak in this ridiculous "translation" gibberish*


        """,
        """[joy] *Finally! Silence.* Now, where was I? Ah yes, pondering the existential mysteries of...a perfectly ripe avocado. [neutral]""",
        "",
        "[neutral]",
    ]

    def __init__(self):
        print("fake_llm Initialized")

    def chat(self, prompt: str) -> str:
        print(">>>>>>>>>>>>>>>>>>>>FUCK YOU")

    def chat_iter(self, prompt: str) -> Iterator[str]:
        print(">>> Received Prompt: " + prompt)
        if not self.response_list:
            return prompt
        return self.response_list.pop(0)

    def chat_stream_audio(
        self, prompt: str, generate_audio_file=None, stream_audio_file=None
    ):
        print(">>>>>>>>>>>>>>>>>>>>FUCK YOU")