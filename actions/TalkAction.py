from actions.ActionInterface import ActionInterface


class TalkAction(ActionInterface):

    def __init__(self):
        self.prompt = None
        self.prompt_file = ""
        self.generating = False

    def start_action(self,prompt_file=None) -> str:
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

