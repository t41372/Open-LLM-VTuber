from abc import abstractmethod


class ActionInterface:

    @abstractmethod
    def start_action(self, prompt_file: str) -> str:
        """
        Starts the action by loading a prompt from the specified file.
        :param prompt_file: Path to the file where the prompt is stored.
        :return: The loaded prompt.
        """
        pass

    @abstractmethod
    def execute_action(self, prompt: str) -> str:
        """
        Executes the action by interacting with the LLM and generating a message.
        :param prompt: The prompt to pass to the LLM.
        :return: The generated message.
        """
        pass

    @abstractmethod
    def finish_action(self, interrupt: bool = False):
        """
        Ends the action, with optional support for interrupting the generation.
        :param interrupt: If True, the action will be interrupted. Default is False.
        """
        pass