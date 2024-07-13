import os

current_dir = os.path.dirname(os.path.abspath(__file__))


PROMPT_DIR = current_dir
PERSONA_PROMPT_DIR = os.path.join(PROMPT_DIR, 'persona')
UTIL_PROMPT_DIR = os.path.join(PROMPT_DIR, 'utils')

def _load_file_content(file_path: str) -> str:
    """Load the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()

def load_persona(persona_name: str) -> str:
    """Load the content of a specific persona prompt file."""
    persona_file_path = os.path.join(PERSONA_PROMPT_DIR, f'{persona_name}.txt')
    return _load_file_content(persona_file_path)
    
def load_util(util_name: str) -> str:
    """Load the content of a specific utility prompt file."""
    util_file_path = os.path.join(UTIL_PROMPT_DIR, f'{util_name}.txt')
    return _load_file_content(util_file_path)

