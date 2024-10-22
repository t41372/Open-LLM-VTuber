import time
import random

from actions.ActionInterface import ActionInterface


class LLMAction(ActionInterface):

    def __init__(self):
        self.prompt = ""
        self.generating = False

    def start_action(self, prompt_file: str) -> str:
        """
        Starts the action by loading a prompt from the specified file.
        """
        try:
            with open(prompt_file, 'r') as file:
                self.prompt = file.read()
                print(f"Prompt loaded: {self.prompt}")
        except FileNotFoundError:
            print(f"Prompt file {prompt_file} not found.")
            self.prompt = "Default prompt"
        return self.prompt


    def execute_action(self, prompt: str) -> str:
        """
        Simulates the execution of the action by asking the LLM to generate a message.
        Here we simulate the LLM generating a response.
        """
        self.generating = True
        print(f"Executing action with prompt: {prompt}")
        time.sleep(2)  # Simulate some delay as if the LLM is generating a response

        # Simulated LLM response generation
        llm_response = f"Generated message based on prompt: {prompt} - [LLM Output]"

        # Mark generation as complete
        self.generating = False
        return llm_response

    def finish_action(self, interrupt: bool = False):
        """
        Ends the action. If interrupted, simulate stopping the generation.
        """
        if interrupt:
            if self.generating:
                print("Interrupting the action...")
                self.generating = False
            else:
                print("No action to interrupt.")
        else:
            print("Action finished successfully.")