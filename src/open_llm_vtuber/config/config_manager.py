import os
import re
import yaml
import chardet
from loguru import logger

def load_config_with_env(path: str) -> dict:
    """
    Load the configuration file with environment variables.
    """
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    # Match ${VAR_NAME}
    pattern = re.compile(r"\$\{(\w+)\}")

    def replacer(match):
        env_var = match.group(1)
        return os.getenv(env_var, match.group(0))

    content = pattern.sub(replacer, content)

    return yaml.safe_load(content)

def load_config_file_with_guess_encoding(file_path: str) -> dict | None:
    if not os.path.exists(file_path):
        logger.error(f"Config file not found: {file_path}")
        return None

    # Try common encodings first
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "ascii"]
    content = None

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                content = file.read()
                break
        except UnicodeDecodeError:
            continue

    if content is None:
        # Try detecting encoding as last resort
        try:
            with open(file_path, "rb") as file:
                raw_data = file.read()
            detected = chardet.detect(raw_data)
            if detected["encoding"]:
                content = raw_data.decode(detected["encoding"])
        except Exception as e:
            logger.error(f"Error detecting encoding for config file {file_path}: {e}")
            return None

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML from {file_path}: {e}")
        return None

def scan_config_alts_directory(config: dict) -> list[str]:
    config_files = ["conf.yaml"]
    config_alts_dir = config.get("CONFIG_ALTS_DIR", "config_alts")
    for root, _, files in os.walk(config_alts_dir):
        for file in files:
            if file.endswith(".yaml"):
                config_files.append(file)
    return config_files

def load_new_config(old_config: dict, filename: str) -> dict | None:
    if filename == "conf.yaml":
        return load_config_with_env("conf.yaml")

    config_alts_dir = old_config.get("CONFIG_ALTS_DIR", "config_alts")
    file_path = os.path.join(config_alts_dir, filename)
    return load_config_file_with_guess_encoding(file_path)

def scan_bg_directory() -> list[str]:
    bg_files = []
    bg_dir = os.path.join("static", "bg")
    for root, _, files in os.walk(bg_dir):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                bg_files.append(file)
    return bg_files

