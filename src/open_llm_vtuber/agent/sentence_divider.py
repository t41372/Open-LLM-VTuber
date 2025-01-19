import re
from typing import List, Tuple, Optional, AsyncIterator
import pysbd
from loguru import logger
from langdetect import detect

# Constants for additional checks
COMMAS = [
    ",", "،", "，", "、", "፣", "၊", ";", "΄", "‛", 
    "।", "﹐", "꓾", "⹁", "︐", "﹑", "､", "،",
]

END_PUNCTUATIONS = [".", "!", "?", "。", "！", "？", "...", "。。。"]
ABBREVIATIONS = [
    "Mr.", "Mrs.", "Dr.", "Prof.", "Inc.", "Ltd.", "Jr.", "Sr.",
    "e.g.", "i.e.", "vs.", "St.", "Rd.", "Dr.",
]

# Set of languages directly supported by pysbd
SUPPORTED_LANGUAGES = {
    'am', 'ar', 'bg', 'da', 'de', 'el', 'en', 'es', 'fa', 
    'fr', 'hi', 'hy', 'it', 'ja', 'kk', 'mr', 'my', 'nl',
    'pl', 'ru', 'sk', 'ur', 'zh'
}

def extract_sentence_by_regex(text: str) -> Tuple[Optional[str], str]:
    """
    Extract the first complete sentence using regex pattern matching.
    Useful as a fallback method when other segmenters fail.

    Args:
        text: Text to extract sentence from

    Returns:
        Tuple[Optional[str], str]: (extracted sentence or None, remaining text)
    """
    if not text:
        return None, ""

    escaped_punctuations = [re.escape(p) for p in END_PUNCTUATIONS]
    pattern = r"(.*?([" + "|".join(escaped_punctuations) + r"]))"

    pos = 0
    while pos < len(text):
        match = re.search(pattern, text[pos:])
        if not match:
            break
        end_pos = pos + match.end(1)
        potential_sentence = text[:end_pos].strip()

        if any(potential_sentence.endswith(abbrev) for abbrev in ABBREVIATIONS):
            pos = end_pos
            continue
        else:
            remaining_text = text[end_pos:].lstrip()
            return potential_sentence, remaining_text
    return None, text

def detect_language(text: str) -> str:
    """
    Detect text language and check if it's supported by pysbd.
    Returns None for unsupported languages.
    """
    try:
        detected = detect(text)
        return detected if detected in SUPPORTED_LANGUAGES else None
    except:
        return None

def is_complete_sentence(text: str) -> bool:
    """
    Check if text ends with sentence-ending punctuation and not abbreviation.
    
    Args:
        text: Text to check
        
    Returns:
        bool: Whether the text is a complete sentence
    """
    text = text.strip()
    if not text:
        return False
        
    if any(text.endswith(abbrev) for abbrev in ABBREVIATIONS):
        return False
        
    return any(text.endswith(punct) for punct in END_PUNCTUATIONS)

def contains_comma(text: str) -> bool:
    """
    Check if text contains any comma.
    
    Args:
        text: Text to check
        
    Returns:
        bool: Whether the text contains a comma
    """
    return any(comma in text for comma in COMMAS)

def comma_splitter(text: str) -> Tuple[str, str]:
    """
    Process text and split it at the first comma.
    Returns the split text and the remaining text.
    
    Args:
        text: Text to split
        
    Returns:
        Tuple[str, str]: (split text, remaining text)
    """
    if not text:
        return [], ""
    
    for comma in COMMAS:
        if comma in text:
            split_text = text.split(comma, 1)
            return split_text[0].strip(), split_text[1].strip()
    return text, ""

def segment_text_by_pysbd(text: str) -> Tuple[List[str], str]:
    """
    Segment text into complete sentences and remaining text.
    Uses pysbd for supported languages, falls back to regex for others.

    Args:
        text: Text to segment into sentences

    Returns:
        Tuple[List[str], str]: (list of complete sentences, remaining incomplete text)
    """
    if not text:
        return [], ""

    try:
        # Detect language
        lang = detect_language(text)
        
        if lang is not None:
            # Use pysbd for supported languages
            segmenter = pysbd.Segmenter(language=lang, clean=False)
            sentences = segmenter.segment(text)
            
            if not sentences:
                return [], text

            # Process all but the last sentence
            complete_sentences = []
            for sent in sentences[:-1]:
                sent = sent.strip()
                if sent:
                    complete_sentences.append(sent)

            # Handle the last sentence
            last_sent = sentences[-1].strip()
            if is_complete_sentence(last_sent):
                complete_sentences.append(last_sent)
                remaining = ""
            else:
                remaining = last_sent
                
        else:
            # Use regex for unsupported languages
            sentence, remaining = extract_sentence_by_regex(text)
            if sentence:
                return [sentence], remaining
            return [], text

        logger.debug(f"Processed sentences: {complete_sentences}, Remaining: {remaining}")
        return complete_sentences, remaining

    except Exception as e:
        logger.error(f"Error in sentence segmentation: {e}")
        # Fallback to regex on any error
        sentence, remaining = extract_sentence_by_regex(text)
        if sentence:
            return [sentence], remaining
        return [], text

class SentenceDivider:
    """
    A class to handle sentence division logic for streaming text responses.
    Supports faster first response by splitting on commas and regular sentence segmentation.
    """

    def __init__(self, faster_first_response: bool = True):
        """
        Initialize the SentenceDivider.

        Args:
            faster_first_response (bool): Whether to split the first sentence at commas for faster response
        """
        self.faster_first_response = faster_first_response
        self._is_first_sentence = True
        self._buffer = ""

    def reset(self):
        """Reset the divider state for a new conversation"""
        self._is_first_sentence = True
        self._buffer = ""

    async def process_stream(self, token_stream) -> AsyncIterator[str]:
        """
        Process a stream of tokens and yield complete sentences.

        Args:
            token_stream: An async iterator yielding tokens

        Yields:
            str: Complete sentences as they are formed
        """
        self._full_response = []

        async for token in token_stream:
            self._buffer += token
            self._full_response.append(token)

            # Process first sentence with comma if enabled
            if self._is_first_sentence and self.faster_first_response and contains_comma(self._buffer):
                sentence, remaining = comma_splitter(self._buffer)
                if sentence.strip():
                    yield sentence.strip()
                self._buffer = remaining
                self._is_first_sentence = False

            # Process buffer when it gets long enough or contains ending punctuation
            if len(self._buffer) >= 25 or any(punct in self._buffer for punct in END_PUNCTUATIONS):
                sentences, remaining = segment_text_by_pysbd(self._buffer)
                for sentence in sentences:
                    if sentence.strip():
                        yield sentence.strip()
                self._buffer = remaining
                self._is_first_sentence = False

        # Process any remaining text
        if self._buffer.strip():
            sentences, remaining = segment_text_by_pysbd(self._buffer)
            for sentence in sentences:
                if sentence.strip():
                    yield sentence.strip()
            if remaining.strip():
                yield remaining.strip()

    @property
    def complete_response(self) -> str:
        """Get the complete response accumulated so far"""
        return "".join(self._full_response)
