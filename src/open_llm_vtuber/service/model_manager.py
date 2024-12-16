from typing import Dict, Any
from loguru import logger

class ModelCache:
    """Manager for caching ASR and TTS models"""
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def set(self, key: str, model: Any) -> None:
        self._cache[key] = model

    def remove(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()


class ModelManager:
    """Manager for working ASR and TTS models"""
    def __init__(self, config: Dict):
        self.config = config
        self._old_config = config.copy()
        self.cache = ModelCache()

    def initialize_models(self) -> None:
        if self.config.get("VOICE_INPUT_ON", False):
            self._init_asr()
        if self.config.get("TTS_ON", False):
            self._init_tts()

    def _init_asr(self) -> None:
        from ..asr.asr_factory import ASRFactory
        asr_model = self.config.get("ASR_MODEL")
        asr_config = self.config.get(asr_model, {})
        self.cache.set("asr", ASRFactory.get_asr_system(asr_model, **asr_config))
        logger.info(f"ASR model {asr_model} loaded successfully")

    def _init_tts(self) -> None:
        from ..tts.tts_factory import TTSFactory
        tts_model = self.config.get("TTS_MODEL")
        tts_config = self.config.get(tts_model, {})
        self.cache.set("tts", TTSFactory.get_tts_engine(tts_model, **tts_config))
        logger.info(f"TTS model {tts_model} loaded successfully")

    def update_models(self, new_config: Dict) -> None:
        try:
            if self._should_reinit_asr(new_config):
                self.config = new_config
                self._update_asr()
            if self._should_reinit_tts(new_config):
                self.config = new_config
                self._update_tts()

            self._old_config = new_config.copy()
            self.config = new_config

        except Exception as e:
            logger.error(f"Error during model update: {e}")
            raise

    def _should_reinit_asr(self, new_config: Dict) -> bool:
        if self._old_config.get("VOICE_INPUT_ON") != new_config.get("VOICE_INPUT_ON"):
            return True
        old_model = self._old_config.get("ASR_MODEL")
        new_model = new_config.get("ASR_MODEL")
        if old_model != new_model:
            return True
        if old_model:
            old_model_config = self._old_config.get(old_model, {})
            new_model_config = new_config.get(old_model, {})
            if old_model_config != new_model_config:
                return True
        return False

    def _should_reinit_tts(self, new_config: Dict) -> bool:
        if self._old_config.get("TTS_ON") != new_config.get("TTS_ON"):
            return True
        old_model = self._old_config.get("TTS_MODEL")
        new_model = new_config.get("TTS_MODEL")
        if old_model != new_model:
            return True
        if old_model:
            old_model_config = self._old_config.get(old_model, {})
            new_model_config = new_config.get(old_model, {})
            if old_model_config != new_model_config:
                return True
        return False

    def _update_asr(self) -> None:
        if self.config.get("VOICE_INPUT_ON", False):
            logger.info("Reinitializing ASR...")
            self._init_asr()
        else:
            logger.info("ASR disabled in new configuration")
            self.cache.remove("asr")

    def _update_tts(self) -> None:
        if self.config.get("TTS_ON", False):
            logger.info("Reinitializing TTS...")
            self._init_tts()
        else:
            logger.info("TTS disabled in new configuration")
            self.cache.remove("tts")
