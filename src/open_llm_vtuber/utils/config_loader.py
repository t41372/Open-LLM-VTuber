import os
import re
import yaml
import chardet
from loguru import logger



def load_config(file_path: str) -> dict | None:
    """
    The ultimate yaml config loader function.
    - It loads a config file with environment variables (e.g. ${VAR_NAME}).
    - It supports weird encodings and will try to guess the encoding.
    - It returns None if an error occurred.
    
    """
    if not os.path.exists(file_path):
        logger.error(f"Config file not found: {file_path}")
        return None

    content = load_text_file_with_guess_encoding(file_path)
    
    if not content:
        logger.error(f"Error reading config file {file_path}")
        return None
    
    # Match ${VAR_NAME}
    pattern = re.compile(r"\$\{(\w+)\}")

    def replacer(match):
        env_var = match.group(1)
        return os.getenv(env_var, match.group(0))

    content = pattern.sub(replacer, content)

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML from {file_path}: {e}")
        return None


def scan_config_alts_directory(config_alts_dir: str) -> list[str]:
    """
    Scan the config_alts directory and return a list of config files.
    
    Parameters:
    - config_alts_dir (str): The path to the config_alts directory.
    
    Returns:
    - list[str]: A list of config files.
    """
    config_files = ["conf.yaml"]
    for root, _, files in os.walk(config_alts_dir):
        for file in files:
            if file.endswith(".yaml"):
                config_files.append(file)
    return config_files


def load_text_file_with_guess_encoding(file_path: str) -> str | None:
    """
    Load a text file with guessed encoding.
    
    Parameters:
    - file_path (str): The path to the text file.
    
    Returns:
    - str: The content of the text file or None if an error occurred.
    """
    
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "ascii"]
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    # If common encodings fail, try chardet to guess the encoding
    try:
        with open(file_path, "rb") as file:
            raw_data = file.read()
        detected = chardet.detect(raw_data)
        if detected["encoding"]:
            return raw_data.decode(detected["encoding"])
    except Exception as e:
        logger.error(f"Error detecting encoding for config file {file_path}: {e}")
    return None

#! Todo: remove this function
def load_new_config(old_config: dict, filename: str) -> dict | None:
    if filename == "conf.yaml":
        return load_config("conf.yaml")

    config_alts_dir = old_config.get("CONFIG_ALTS_DIR", "config_alts")
    file_path = os.path.join(config_alts_dir, filename)
    return load_config(file_path)


def scan_bg_directory() -> list[str]:
    bg_files = []
    bg_dir = os.path.join("static", "bg")
    for root, _, files in os.walk(bg_dir):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                bg_files.append(file)
    return bg_files
