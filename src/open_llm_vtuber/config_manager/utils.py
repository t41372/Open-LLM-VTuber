# config_manager/utils.py
import yaml
from pathlib import Path
from typing import Type, Optional, Union, Dict, Any, TypeVar
from pydantic import BaseModel, ValidationError
import os
import re
import chardet
from loguru import logger

from .main import Config
from .i18n import Description, MultiLingualString

T = TypeVar("T", bound=BaseModel)

def load_config(config_path: str, model: Type[T] = None) -> T:
    """
    Load configuration from a YAML file and validate it against a Pydantic model.

    Args:
        config_path: Path to the YAML configuration file.
        model: Pydantic model class to validate against (optional).

    Returns:
        Validated configuration object.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML file is invalid.
        ValidationError: If the configuration fails validation.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise

    if model is None:
        from .main import Config
        model = Config

    try:
        return model.model_validate(config_data)
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        raise


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


def save_config(config: BaseModel, config_path: Union[str, Path]):
    """
    Saves a Pydantic model to a YAML configuration file.

    Args:
        config: The Pydantic model to save.
        config_path: Path to the YAML configuration file.
    """
    config_file = Path(config_path)
    config_data = config.model_dump(
        by_alias=True, exclude_unset=True, exclude_none=True
    )

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error writing YAML file: {e}")


def create_config_template(
    model: Type[BaseModel] = Config,
    lang_code: str = "en",
    include_defaults: bool = False,
    skip_comments: bool = False,
) -> str:
    """
    Creates a YAML configuration template with descriptions and options for the given model.

    Args:
        model: The Pydantic model to create a template for.
        lang_code: The language code for the descriptions.
        include_defaults: Whether to include default values in the template.
        skip_comments: Whether to skip comments in the template.

    Returns:
        A YAML string representing the configuration template.
    """
    config_data: Dict[str, Any] = {}

    def process_model(m: Type[BaseModel], data: Dict[str, Any]):
        for field_name, field_info in m.model_fields.items():
            # Use alias if available
            config_key = field_info.alias or field_name

            field_description = m.get_field_description(field_name, lang_code)
            field_notes = m.get_field_notes(field_name, lang_code)
            options = m.get_field_options(field_name)

            if not skip_comments:
                if field_description:
                    if field_notes:
                        data[config_key] = f"# {field_description} ({field_notes})"
                    else:
                        data[config_key] = f"# {field_description}"
                if options:
                    data[config_key] = f"# options: {options}"

            if hasattr(field_info.annotation, "__args__"):
                # Handle Union types (Optional, etc.)
                type_args = field_info.annotation.__args__
                if type(None) in type_args:
                    # Optional field
                    if include_defaults:
                        data[config_key] = field_info.default
                    else:
                        data[config_key] = None
                elif any(
                    issubclass(t, BaseModel) for t in type_args if isinstance(t, type)
                ):
                    # Union of BaseModel types
                    for t in type_args:
                        if isinstance(t, type) and issubclass(t, BaseModel):
                            sub_data: Dict[str, Any] = {}
                            process_model(t, sub_data)
                            data[config_key] = sub_data
                            break  # Assume only one BaseModel type in the Union
            elif issubclass(field_info.annotation, BaseModel):
                # Nested model
                sub_data: Dict[str, Any] = {}
                process_model(field_info.annotation, sub_data)
                data[config_key] = sub_data
            else:
                # Regular field
                if include_defaults and field_info.default is not None:
                    data[config_key] = field_info.default
                elif field_info.is_required():
                    data[config_key] = "..."

    process_model(model, config_data)
    return yaml.dump(config_data, allow_unicode=True, sort_keys=False, indent=2)


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
    config_files.append(
        {
            "filename": "conf.yaml",
            "name": default_config.get("CONF_NAME", "conf.yaml")
            if default_config
            else "conf.yaml",
        }
    )

    # Scan other configs
    for root, _, files in os.walk(config_alts_dir):
        for file in files:
            if file.endswith(".yaml"):
                config = load_config(os.path.join(root, file))
                config_files.append(
                    {
                        "filename": file,
                        "name": config.get("CONF_NAME", file) if config else file,
                    }
                )

    return config_files


def scan_bg_directory() -> list[str]:
    bg_files = []
    bg_dir = os.path.join("static", "bg")
    for root, _, files in os.walk(bg_dir):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png", ".gif")):
                bg_files.append(file)
    return bg_files
