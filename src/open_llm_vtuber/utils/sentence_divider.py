from typing import List, Tuple, Optional
from loguru import logger
import pysbd
import re
from langdetect import detect

# Constants for additional checks
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

def extract_sentence_regex(text: str) -> Tuple[Optional[str], str]:
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

def process_text_stream(text: str) -> Tuple[List[str], str]:
    """
    Process text stream and return complete sentences and remaining text.
    Uses pysbd for supported languages, falls back to regex for others.
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
            sentence, remaining = extract_sentence_regex(text)
            if sentence:
                return [sentence], remaining
            return [], text

        logger.debug(f"Processed sentences: {complete_sentences}, Remaining: {remaining}")
        return complete_sentences, remaining

    except Exception as e:
        logger.error(f"Error in sentence segmentation: {e}")
        # Fallback to regex on any error
        sentence, remaining = extract_sentence_regex(text)
        if sentence:
            return [sentence], remaining
        return [], text
