from typing import AsyncIterator, Tuple, Callable
from functools import wraps
from .output_types import Actions, SentenceOutput
from ..utils.tts_preprocessor import tts_filter as filter_text
from ..live2d_model import Live2dModel
from ..utils.sentence_divider import SentenceDivider
from ..config_manager import TTSPreprocessorConfig


def sentence_divider(faster_first_response: bool = True, segment_method: str = "pysbd"):
    """
    Decorator that transforms token stream into sentences

    Args:
        faster_first_response: Whether to respond faster
        segment_method: Method to use for sentence segmentation
    """

    def decorator(
        func: Callable[..., AsyncIterator[str]],
    ) -> Callable[..., AsyncIterator[str]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[str]:
            divider = SentenceDivider(
                faster_first_response=faster_first_response,
                segment_method=segment_method,
            )
            token_stream = func(*args, **kwargs)

            async for sentence in divider.process_stream(token_stream):
                yield sentence

        return wrapper

    return decorator


def actions_extractor(live2d_model: Live2dModel):
    """
    Decorator that extracts actions from sentences

    Args:
        live2d_model: Live2D model to use for emotion extraction
    """

    def decorator(
        func: Callable[..., AsyncIterator[str]],
    ) -> Callable[..., AsyncIterator[Tuple[str, Actions]]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[Tuple[str, Actions]]:
            sentence_stream = func(*args, **kwargs)

            async for sentence in sentence_stream:
                actions = Actions()
                expressions = live2d_model.extract_emotion(sentence)
                if expressions:
                    actions.expressions = expressions
                yield sentence, actions

        return wrapper

    return decorator


def display_processor():
    """
    Decorator that processes text for display.
    Should be applied after actions_extractor and before tts_filter.
    """

    def decorator(
        func: Callable[..., AsyncIterator[Tuple[str, Actions]]],
    ) -> Callable[..., AsyncIterator[Tuple[str, str, Actions]]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[Tuple[str, str, Actions]]:
            stream = func(*args, **kwargs)
            async for original, actions in stream:
                # Future: Add display text processing here
                display = original  # Currently just passing through
                yield original, display, actions

        return wrapper

    return decorator


def tts_filter(tts_preprocessor_config: TTSPreprocessorConfig = None):
    """
    Decorator that filters text for TTS using provided configuration

    Args:
        tts_preprocessor_config: Configuration for TTS preprocessing
    """

    def decorator(
        func: Callable[..., AsyncIterator[Tuple[str, str, Actions]]],
    ) -> Callable[..., AsyncIterator[SentenceOutput]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[SentenceOutput]:
            sentence_stream = func(*args, **kwargs)

            config = tts_preprocessor_config or TTSPreprocessorConfig()

            async for original, display, actions in sentence_stream:
                filtered = filter_text(
                    text=display,
                    remove_special_char=config.remove_special_char,
                    ignore_brackets=config.ignore_brackets,
                    ignore_parentheses=config.ignore_parentheses,
                    ignore_asterisks=config.ignore_asterisks,
                    translator=None,  # Translation handled separately
                )
                yield SentenceOutput(
                    display_sentences=[display],
                    tts_sentences=[filtered],
                    actions=actions,
                )

        return wrapper

    return decorator
