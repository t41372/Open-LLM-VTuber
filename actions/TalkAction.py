from actions.ActionInterface import ActionInterface
from llm.llm_factory import LLMFactory
from main import OpenLLMVTuberMain


class TalkAction(ActionInterface):

    def __init__(self):
        self.prompt = None
        self.prompt_file = ""
        self.generating = False
        self.is_blocking_action = False

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
        return None

    def block_llm_generation(self):
        OpenLLMVTuberMain().is_blocking_event.set()
        return None
