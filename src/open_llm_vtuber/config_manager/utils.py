# config_manager/utils.py
import yaml
from pathlib import Path
from typing import Type, Optional, Union, Dict, Any
from pydantic import BaseModel, ValidationError

from .main import Config
from .i18n import Description, MultiLingualString


def load_config(
    config_path: Union[str, Path], model: Type[BaseModel] = Config
) -> BaseModel:
    """
    Loads the YAML configuration file and parses it into a Pydantic model.

    Args:
        config_path: Path to the YAML configuration file.
        model: The Pydantic model to parse the configuration into (default: Config).

    Returns:
        An instance of the specified Pydantic model.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValidationError: If the configuration file is invalid.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    config_file = Path(config_path)
    if not config_file.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    try:
        return model.model_validate(config_data)
    except ValidationError as e:
        raise ValidationError(f"Error validating configuration: {e}")


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
