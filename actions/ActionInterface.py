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

    def finish_action(self):
        """
        Starts the action by loading a prompt from the specified file.
        :param prompt_file: Path to the file where the prompt is stored.
        :return: The loaded prompt.
        """
        pass

    def block_llm_generation(self):
        """
        Blocks LLM generation to perform action.
        """
        pass

    def load_action_memory(self):
        """
        Loads action memory blocks to the LLM client
        """
        pass

