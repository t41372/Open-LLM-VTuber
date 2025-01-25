from typing import AsyncIterator, Tuple, Callable
from functools import wraps
from .output_types import Actions, SentenceOutput
from ..utils.tts_preprocessor import tts_filter as filter_text
from ..live2d_model import Live2dModel
from .sentence_divider import SentenceDivider

def sentence_divider(faster_first_response: bool = True, segment_method: str = "pysbd"):
    """
    Decorator that transforms token stream into sentences
    
    Args:
        faster_first_response: Whether to respond faster
        segment_method: Method to use for sentence segmentation
    """
    def decorator(func: Callable[..., AsyncIterator[str]]) -> Callable[..., AsyncIterator[str]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[str]:
            divider = SentenceDivider(
                faster_first_response=faster_first_response,
                segment_method=segment_method
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
    def decorator(func: Callable[..., AsyncIterator[str]]) -> Callable[..., AsyncIterator[Tuple[str, Actions]]]:
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

def tts_filter(
    remove_special_char: bool = True,
    ignore_brackets: bool = True, 
    ignore_parentheses: bool = True,
    ignore_asterisks: bool = True
):
    """
    Decorator that filters text for TTS
    
    Args:
        remove_special_char: Whether to remove special characters
        ignore_brackets: Whether to ignore text in brackets
        ignore_parentheses: Whether to ignore text in parentheses 
        ignore_asterisks: Whether to ignore text with asterisks
    """
    def decorator(
        func: Callable[..., AsyncIterator[Tuple[str, Actions]]]
    ) -> Callable[..., AsyncIterator[Tuple[str, str, Actions]]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[Tuple[str, str, Actions]]:
            sentence_stream = func(*args, **kwargs)

            async for original, actions in sentence_stream:
                filtered = filter_text(
                    text=original,
                    remove_special_char=remove_special_char,
                    ignore_brackets=ignore_brackets,
                    ignore_parentheses=ignore_parentheses,
                    ignore_asterisks=ignore_asterisks,
                    translator=None,  # Translation handled separately
                )
                yield original, filtered, actions

        return wrapper
    return decorator

def display_processor():
    """
    Decorator that processes text for display
    Currently just passes through the input
    """
    def decorator(
        func: Callable[..., AsyncIterator[Tuple[str, str, Actions]]]
    ) -> Callable[..., AsyncIterator[Tuple[str, str, Actions]]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterator[Tuple[str, str, Actions]]:
            stream = func(*args, **kwargs)
            async for display, filtered, actions in stream:
                # Future: Add display text processing here
                yield SentenceOutput(
                    display_sentences=[display],
                    tts_sentences=[filtered],
                    actions=actions
                )
                
        return wrapper
    return decorator 
