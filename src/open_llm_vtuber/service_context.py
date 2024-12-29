import os
import json
from typing import Dict

from loguru import logger
from fastapi import APIRouter, WebSocket

from prompts import prompt_loader
from .live2d_model import Live2dModel
from .asr.asr_interface import ASRInterface
from .tts.tts_interface import TTSInterface
from .llm.llm_interface import LLMInterface
from .translate.translate_interface import TranslateInterface

from .asr.asr_factory import ASRFactory
from .tts.tts_factory import TTSFactory
from .llm.llm_factory import LLMFactory
from .translate.translate_factory import TranslateFactory

from .config_manager import (
    Config,
    CharacterConfig,
    SystemConfig,
    ASRConfig,
    TTSConfig,
    LLMConfig,
    read_yaml,
    validate_config,
)


class ServiceContext:
    """Initializes, stores, and updates the asr, tts, llm instance for a connected client."""

    def __init__(self):
        self.config: Config = None
        self.system_config: SystemConfig = None
        self.character_config: CharacterConfig = None
        self.asr_config: ASRConfig = None
        self.tts_config: TTSConfig = None
        self.llm_config: LLMConfig = None
        # self.translate_config: TranslatorConfig = None

        self.live2d_model: Live2dModel = None
        self.asr_engine: ASRInterface = None
        self.tts_engine: TTSInterface = None
        self.llm_engine: LLMInterface = None
        # self.translate: TranslateInterface

        self.llm_persona_choice: str = None
        self.llm_text_prompt: str = None

    def __str__(self):
        return (
            f"ServiceContext:\n"
            f"  System Config: {'Loaded' if self.system_config else 'Not Loaded'}\n"
            f"    Details: {json.dumps(self.system_config.model_dump(), indent=6) if self.system_config else 'None'}\n"
            f"  Live2D Model: {self.live2d_model.model_info if self.live2d_model else 'Not Loaded'}\n"
            f"  ASR Engine: {type(self.asr_engine).__name__ if self.asr_engine else 'Not Loaded'}\n"
            f"    Config: {json.dumps(self.asr_config.model_dump(), indent=6) if self.asr_config else 'None'}\n"
            f"  TTS Engine: {type(self.tts_engine).__name__ if self.tts_engine else 'Not Loaded'}\n"
            f"    Config: {json.dumps(self.tts_config.model_dump(), indent=6) if self.tts_config else 'None'}\n"
            f"  LLM Engine: {type(self.llm_engine).__name__ if self.llm_engine else 'Not Loaded'}\n"
            f"    Config: {json.dumps(self.llm_config.model_dump(), indent=6) if self.llm_config else 'None'}\n"
            f"  LLM Provider: {self.llm_config.llm_provider if self.llm_config else 'Not Set'}\n"
            f"  LLM Persona: {self.llm_persona_choice or 'Not Set'}"
        )

    # ==== Initializers

    def load_cache(
        self,
        config: Config,
        system_config: SystemConfig,
        character_config: CharacterConfig,
        live2d_model: Live2dModel,
        asr_engine: ASRInterface,
        tts_engine: TTSInterface,
        llm_engine: LLMInterface,
    ) -> None:
        """
        Load the ServiceContext with the reference of the provided instances.
        Pass by reference so no reinitialization will be done.
        """
        if not character_config:
            raise ValueError("character_config cannot be None")
        if not system_config:
            raise ValueError("system_config cannot be None")

        self.config = config
        self.system_config = system_config
        self.character_config = character_config
        self.live2d_model = live2d_model
        self.asr_engine = asr_engine
        self.tts_engine = tts_engine
        self.llm_engine = llm_engine

        logger.debug(
            f"Loaded service context with character config: {character_config}"
        )

    def load_from_config(self, config: Config) -> None:
        """
        Load the ServiceContext with the config.
        Reinitialize the instances if the config is different.

        Parameters:
        - config (Dict): The configuration dictionary.
        """
        # store typed config references
        self.config = config
        self.system_config = config.system_config or self.system_config
        self.character_config = config.character_config or self.character_config
        # update all sub-configs

        # init live2d from character config
        self.init_live2d(self.character_config.live2d_model)

        # init asr from character config
        self.init_asr(self.character_config.asr_config)

        # init tts from character config
        self.init_tts(self.character_config.tts_config)

        # init llm from character config
        self.init_llm(
            self.character_config.llm_config,
            self.character_config.persona_choice,
            self.character_config.default_persona_prompt_in_yaml,
        )

    def init_live2d(self, live2d_model_name: str) -> None:
        try:
            self.live2d_model = Live2dModel(live2d_model_name)
        except Exception as e:
            print(f"Error initializing Live2D: {e}")
            print("Proceed without Live2D.")

    def init_asr(self, asr_config: ASRConfig) -> None:
        if not self.asr_engine or (self.asr_config != asr_config):
            logger.info(asr_config)
            logger.info(vars(asr_config).get(asr_config.asr_model))
            self.asr_engine = ASRFactory.get_asr_system(
                asr_config.asr_model,
                **getattr(asr_config, asr_config.asr_model.lower()).model_dump(),
            )
            # saving config should be done after successful initialization
            self.asr_config = asr_config
        else:
            logger.debug("ASR already initialized with the same config.")

    def init_tts(self, tts_config: TTSConfig) -> None:
        if not self.tts_engine or (self.tts_config != tts_config):
            self.tts_engine = TTSFactory.get_tts_engine(
                tts_config.tts_model,
                **getattr(tts_config, tts_config.tts_model.lower()).model_dump(),
            )
            # saving config should be done after successful initialization
            self.tts_config = tts_config
        else:
            logger.debug("TTS already initialized with the same config.")

    # TODO - implement llm update logic after separating the memory and system prompt
    def init_llm(
        self, llm_config: LLMConfig, persona_choice: str, text_prompt: str
    ) -> None:
        # Use existing values if new parameters are None
        new_llm_config = llm_config or self.llm_config
        new_llm_provider = llm_config.llm_provider or self.llm_config.llm_provider
        new_persona_choice = persona_choice or self.llm_persona_choice
        new_text_prompt = text_prompt or self.llm_text_prompt

        # Check if any parameters have changed
        if (
            self.llm_engine is not None
            and new_llm_provider == self.character_config.llm_config.llm_provider
            and new_llm_config == self.llm_config
            and new_persona_choice == self.llm_persona_choice
            and new_text_prompt == self.llm_text_prompt
        ):
            logger.debug("LLM already initialized with the same config.")
            return

        system_prompt = self.get_system_prompt(new_persona_choice, new_text_prompt)

        self.llm_engine = LLMFactory.create_llm(
            llm_provider=new_llm_provider,
            SYSTEM_PROMPT=system_prompt,
            **getattr(new_llm_config, new_llm_provider).model_dump(),
        )

        # Save the current configuration
        self.llm_provider = new_llm_provider
        self.llm_config = new_llm_config
        self.llm_persona_choice = new_persona_choice
        self.llm_text_prompt = new_text_prompt

    # ==== utils

    def get_system_prompt(self, persona_choice: str, text_prompt: str) -> str:
        """
        Fetch the persona prompt, construct system prompt, and return the
        system prompt. text_prompt will be used if persona_choice is None.
        """
        logger.debug(f"persona_choice: {persona_choice}, text_prompt: {text_prompt}")

        system_prompt = (
            prompt_loader.load_persona(persona_choice)
            if persona_choice
            else text_prompt
        )

        system_prompt += prompt_loader.load_util(
            self.system_config.live2d_expression_prompt
        ).replace("[<insert_emomap_keys>]", self.live2d_model.emo_str)

        logger.debug("\n === System Prompt ===")
        logger.debug(system_prompt)

        return system_prompt

    async def handle_config_switch(
        self,
        websocket: WebSocket,
        config_file_name: str,
    ) -> None:
        """
        Handle the configuration switch request.
        Change the configuration to a new config and notify the client.

        Parameters:
        - websocket (WebSocket): The WebSocket connection.
        - config_file_name (str): The name of the configuration file.
        """
        try:
            new_character_config_data = None

            if config_file_name == "conf.yaml":
                # Load base config
                new_character_config_data = read_yaml("conf.yaml").get(
                    "character_config"
                )
            else:
                # Load alternative config and merge with base config
                config_alts_dir = self.system_config.config_alts_dir
                file_path = os.path.join(config_alts_dir, config_file_name)

                alt_config_data = read_yaml(file_path).get("character_config")

                # Start with original config data and perform a deep merge
                new_character_config_data = self.config.character_config.model_dump()
                new_character_config_data = deep_merge(new_character_config_data, alt_config_data)
                logger.warning(f"New config data: {new_character_config_data}")

            if new_character_config_data:
                new_config = {
                    "system_config": self.system_config.model_dump(),
                    "character_config": new_character_config_data,
                }
                new_config = validate_config(new_config)
                logger.debug(f"Current config: {self}")
                self.load_from_config(new_config)
                logger.debug(f"New config: {self}")

                # Send responses to client
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "config-switched",
                            "message": f"Switched to config: {config_file_name}",
                        }
                    )
                )

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "config-info",
                            "conf_name": self.character_config.conf_name,
                            "conf_uid": self.character_config.conf_uid,
                        }
                    )
                )

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "set-model",
                            "model_info": self.live2d_model.model_info,
                        }
                    )
                )
                logger.info(f"Configuration switched to {config_file_name}")
            else:
                raise ValueError(
                    f"Failed to load configuration from {config_file_name}"
                )

        except Exception as e:
            logger.error(f"Error switching configuration: {e}")
            logger.debug(self)
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": f"Error switching configuration: {str(e)}",
                    }
                )
            )
            raise e

def deep_merge(dict1, dict2):
    """
    Recursively merges dict2 into dict1, prioritizing values from dict2.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
