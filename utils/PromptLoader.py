from loguru import logger


class PromptLoader:
    _instance = None

    def __init__(self):
        self.prompt = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PromptLoader, cls).__new__(cls)
        return cls._instance

    def get_prompt_from_file(self, prompt_file):
        try:
            with open(prompt_file, 'r') as file:
                self.prompt = file.read()
            logger.info(f"Prompt loaded: {self.prompt}")
        except FileNotFoundError:
            logger.info(f"Prompt file {prompt_file} not found.")
            self.prompt = "Default prompt"
        return self.prompt
