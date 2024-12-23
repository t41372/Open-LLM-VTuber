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


def scan_config_alts_directory(config_alts_dir: str) -> list[dict]:
    """
    Scan the config_alts directory and return a list of config information.
    Each config info contains the filename and its display name from the config.
    
    Parameters:
    - config_alts_dir (str): The path to the config_alts directory.
    
    Returns:
    - list[dict]: A list of dicts containing config info:
        - filename: The actual config file name
        - name: Display name from config, falls back to filename if not specified
    """
    config_files = []
    
    # Add default config first
    default_config = load_config("conf.yaml")
    config_files.append({
        "filename": "conf.yaml",
        "name": default_config.get("CONF_NAME", "conf.yaml") if default_config else "conf.yaml"
    })
    
    # Scan other configs
    for root, _, files in os.walk(config_alts_dir):
        for file in files:
            if file.endswith(".yaml"):
                config = load_config(os.path.join(root, file))
                config_files.append({
                    "filename": file,
                    "name": config.get("CONF_NAME", file) if config else file
                })
                
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


def scan_bg_directory() -> list[str]:
    bg_files = []
    bg_dir = os.path.join("static", "bg")
    for root, _, files in os.walk(bg_dir):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                bg_files.append(file)
    return bg_files
