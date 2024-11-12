from actions.ActionInterface import ActionInterface
from OpenLLMVtuber import OpenLLMVTuberMain


class TalkAction(ActionInterface):

    def __init__(self):
        self.prompt = None
        self.prompt_file = ""
        self.generating = False
        self.not_is_blocking_action = True
        self.requires_input = True

    def start_action(self, prompt_file=None) -> str:
        """
        Starts the action by loading a prompt from the specified file.
        """
        if prompt_file is not None:
            self.prompt_file = prompt_file
        try:
            with open(self.prompt_file, 'r') as file:
                self.prompt = file.read()
                print(f"Prompt loaded: {self.prompt}")
        except FileNotFoundError:
            print(f"Prompt file {self.prompt_file} not found.")
            self.prompt = "Default prompt"
        return self.prompt

    def finish_action(self):
        """
        Starts the action by loading a prompt from the specified file.
        """
        if self.not_is_blocking_action:
            OpenLLMVTuberMain().not_is_blocking_event.set()
        del self
        return None

    def block_llm_generation(self):
        OpenLLMVTuberMain().not_is_blocking_event.clear()
        return None
