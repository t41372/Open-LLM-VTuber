from typing import Dict, Any, Tuple
from loguru import logger
import os
import numpy as np
import asyncio
import json

from ..service.model_manager import ModelManager
from ..main import OpenLLMVTuberMain 
from ..live2d_model import Live2dModel

class ServiceContext:
    def __init__(self, config: Dict, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        self.model_manager.initialize_models()

        self.live2d_model = Live2dModel(self.config["LIVE2D_MODEL"])

        custom_asr = self.model_manager.cache.get("asr")
        custom_tts = self.model_manager.cache.get("tts")
        self.open_llm_vtuber = OpenLLMVTuberMain(
            self.config,
            custom_asr=custom_asr,
            custom_tts=custom_tts
        )


    def switch_config(self, new_config: Dict) -> Tuple[Live2dModel, OpenLLMVTuberMain]:
        self.model_manager.update_models(new_config)
        self.config.update(new_config)

        self.live2d_model = Live2dModel(self.config["LIVE2D_MODEL"])

        custom_asr = self.model_manager.cache.get("asr")
        custom_tts = self.model_manager.cache.get("tts")

        self.open_llm_vtuber = OpenLLMVTuberMain(
            self.config,
            custom_asr=custom_asr,
            custom_tts=custom_tts
        )
        return self.live2d_model, self.open_llm_vtuber
