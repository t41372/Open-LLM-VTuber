from dataclasses import dataclass, asdict
from typing import List, Optional
from abc import ABC, abstractmethod


@dataclass
class Actions:
    """Represents actions that can be performed alongside text output"""

    expressions: Optional[List[str] | List[int]] = None
    pictures: Optional[List[str]] = None
    sounds: Optional[List[str]] = None

    def to_dict(self) -> dict:
        """Convert Actions object to a dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class AgentOutputBase(ABC):
    """Base class for agent outputs that can be iterated"""

    @abstractmethod
    def __aiter__(self):
        """Make the output iterable"""
        pass


@dataclass
class SentenceOutput(AgentOutputBase):
    """Output type for text-based responses"""

    display_sentences: List[str]  # Text for display
    tts_sentences: List[str]  # Text for TTS
    actions: Actions

    async def __aiter__(self):
        """Iterate through sentences and their actions"""
        for display, tts in zip(self.display_sentences, self.tts_sentences):
            yield display, tts, self.actions


@dataclass
class AudioOutput(AgentOutputBase):
    """Output type for audio-based responses"""

    audio_path: str
    display_text: str  # Text for display
    transcript: str  # Original transcript
    actions: Actions

    async def __aiter__(self):
        """Iterate through audio segments and their actions"""
        yield self.audio_path, self.display_text, self.transcript, self.actions
