import re
import unicodedata
from loguru import logger
from ..translate.translate_interface import TranslateInterface


def tts_filter(
    text: str,
    remove_special_char: bool,
    ignore_brackets: bool,
    ignore_parentheses: bool,
    ignore_asterisks: bool,
    translator: TranslateInterface | None = None,
) -> str:
    """
    Filter or do anything to the text before TTS generates the audio.
    Changes here do not affect subtitles or LLM's memory. The generated audio is
    the only affected thing.

    Args:
        text (str): The text to filter.
        remove_special_char (bool): Whether to remove special characters.
        ignore_brackets (bool): Whether to ignore text within brackets.
        ignore_parentheses (bool): Whether to ignore text within parentheses.
        ignore_asterisks (bool): Whether to ignore text within asterisks.
        translator (TranslateInterface, optional):
            The translator to use. If None, we'll skip the translation. Defaults to None.

    Returns:
        str: The filtered text.
    """
    if ignore_asterisks:
        try:
            text = filter_asterisks(text)
        except Exception as e:
            logger.warning(f"Error ignoring asterisks: {e}")
            logger.warning(f"Text: {text}")
            logger.warning("Skipping...")

    if ignore_brackets:
        try:
            text = filter_brackets(text)
        except Exception as e:
            logger.warning(f"Error ignoring brackets: {e}")
            logger.warning(f"Text: {text}")
            logger.warning("Skipping...")
    if ignore_parentheses:
        try:
            text = filter_parentheses(text)
        except Exception as e:
            logger.warning(f"Error ignoring parentheses: {e}")
            logger.warning(f"Text: {text}")
            logger.warning("Skipping...")
    if remove_special_char:
        try:
            text = remove_special_characters(text)
        except Exception as e:
            logger.warning(f"Error removing special characters: {e}")
            logger.warning(f"Text: {text}")
            logger.warning("Skipping...")
    if translator:
        try:
            logger.info("Translating...")
            text = translator.translate(text)
            logger.info(f"Translated: {text}")
        except Exception as e:
            logger.critical(f"Error translating: {e}")
            logger.critical(f"Text: {text}")
            logger.warning("Skipping...")

    logger.warning(f"Filtered text: {text}")
    return text


def remove_special_characters(text: str) -> str:
    """
    Filter text to remove all non-letter, non-number, and non-punctuation characters.

    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.
    """
    normalized_text = unicodedata.normalize("NFKC", text)

    def is_valid_char(char: str) -> bool:
        category = unicodedata.category(char)
        return (
            category.startswith("L")
            or category.startswith("N")
            or category.startswith("P")
            or char.isspace()
        )

    filtered_text = "".join(char for char in normalized_text if is_valid_char(char))
    return filtered_text


def filter_brackets(text: str) -> str:
    """
    Filter text to remove all text within brackets, handling nested cases.

    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.

    Examples:
        >>> ignore_brackets("Hello [world [nested] test]")
        'Hello '
        >>> ignore_brackets("[[]]")
        ''
        >>> ignore_brackets("Text [here] and [there]")
        'Text  and '
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    if not text:
        return text

    # Handle nested brackets
    stack = []
    for i, char in enumerate(text):
        if char == "[":
            stack.append(i)
        elif char == "]":
            if stack:
                start = stack.pop()
                if not stack:  # Only replace if we've closed all nested brackets
                    text = text[:start] + " " + text[i + 1 :]

    return re.sub(r"\s+", " ", text).strip()


def filter_parentheses(text: str) -> str:
    """
    Filter text to remove all text within parentheses, handling nested cases.

    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.

    Examples:
        >>> ignore_parentheses("Hello (world (nested) test)")
        'Hello '
        >>> ignore_parentheses("((()))")
        ''
        >>> ignore_parentheses("Text (here) and (there)")
        'Text  and '
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    if not text:
        return text

    # Handle nested parentheses
    stack = []
    for i, char in enumerate(text):
        if char == "(":
            stack.append(i)
        elif char == ")":
            if stack:
                start = stack.pop()
                if not stack:  # Only replace if we've closed all nested parentheses
                    text = text[:start] + " " + text[i + 1 :]

    return re.sub(r"\s+", " ", text).strip()


def filter_asterisks(text):
    """
    Removes text enclosed within single asterisks (*) from a string.

    Args:
      text: The input string.

    Returns:
      The string with asterisk-enclosed text removed.
    """

    # Use a regular expression to find and replace text within asterisks.
    # The regex pattern `\*([^*]+)\*` matches:
    #   \*     - A literal asterisk
    #   (      - Start of a capturing group
    #   [^*]+ - One or more characters that are NOT asterisks
    #   )      - End of the capturing group
    #   \*     - A literal asterisk
    # The replacement string is an empty string, effectively removing the matched text.
    # re.DOTALL flag is not needed here as we explicitly exclude asterisks in the character set.

    filtered_text = re.sub(r"\*([^*]+)\*", "", text)
    return filtered_text


if __name__ == "__main__":
    while True:
        print(remove_special_characters(input(">> ")))
