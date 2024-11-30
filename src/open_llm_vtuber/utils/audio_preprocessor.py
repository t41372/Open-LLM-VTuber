import unicodedata
from ..translate.translate_interface import TranslateInterface


def audio_filter(
    text: str, remove_special_char: bool, translator: TranslateInterface | None = None
) -> str:
    """
    Filter or do anything to the text before TTS generates the audio.
    Changes here do not affect subtitles or LLM's memory. The generated audio is
    the only affected thing.

    Args:
        text (str): The text to filter.
        remove_special_char (bool): Whether to remove special characters.
        
        translator (TranslateInterface, optional): The translator to use. Defaults to None.

    Returns:
        str: The filtered text.
    """

    if remove_special_char:
        try:
            text = remove_special_characters(text)
        except Exception as e:
            print(f"Error removing special characters: {e}")
            print(f"Text: {text}")
            print("Skipping...")
    if translator:
        try:
            print("Translating...")
            text = translator.translate(text)
            print(f"Translated: {text}")
        except Exception as e:
            print(f"Error translating: {e}")
            print(f"Text: {text}")
            print("Skipping...")
        
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


if __name__ == "__main__":
    while True:
        print(remove_special_characters(input(">> ")))
