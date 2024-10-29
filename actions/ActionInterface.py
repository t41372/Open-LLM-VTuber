from abc import abstractmethod

from actions.ActionsMeta import ActionsMeta


class ActionInterface(metaclass=ActionsMeta):

    @abstractmethod
    def start_action(self, prompt_file: str) -> str:
        """
        Starts the action by loading a prompt from the specified file.
        :param prompt_file: Path to the file where the prompt is stored.
        :return: The loaded prompt.
        """
        pass

