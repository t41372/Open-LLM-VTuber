import re


def is_complete_sentence(input_text: str) -> bool:
    """
    Check if the text is a complete sentence.
    text: str
        the text to check
    """

    white_list = [
        "...",
        "Dr.",
        "Mr.",
        "Ms.",
        "Mrs.",
        "Jr.",
        "Sr.",
        "St.",
        "Ave.",
        "Rd.",
        "Blvd.",
        "Dept.",
        "Univ.",
        "Prof.",
        "Ph.D.",
        "M.D.",
        "U.S.",
        "U.K.",
        "U.N.",
        "E.U.",
        "U.S.A.",
        "U.K.",
        "U.S.S.R.",
        "U.A.E.",
    ]

    for item in white_list:
        if input_text.strip().endswith(item):
            return False

    punctuation_blacklist = [
        ".",
        "?",
        "!",
        "。",
        "；",
        "？",
        "！",
        "…",
        "〰",
        "〜",
        "～",
        "！",
    ]
    return any(input_text.strip().endswith(punct) for punct in punctuation_blacklist)


# TODO Need more work
def extract_complete_sentence(target_text) -> tuple[str, str]:
    """
    Extract the first complete sentence from the text.

    Parameters:
    - target_text (str): The text to extract the sentence from.

    Returns:
    - str: The extracted sentence.
    - str: The remaining text after the extracted sentence.
    """

    end_punctuations = [".", "!", "?", "。", "！", "？", "...", "。。。"]
    abbreviations = [
        "Mr.",
        "Mrs.",
        "Dr.",
        "Prof.",
        "Inc.",
        "Ltd.",
        "Jr.",
        "Sr.",
        "e.g.",
        "i.e.",
        "vs.",
        "St.",
        "Rd.",
        "Dr.",
    ]

    escaped_punctuations = [re.escape(p) for p in end_punctuations]
    pattern = r"(.*?([" + "|".join(escaped_punctuations) + r"]))"

    pos = 0
    while pos < len(target_text):
        match = re.search(pattern, target_text[pos:])
        if not match:
            break
        end_pos = pos + match.end(1)
        potential_sentence = target_text[:end_pos].strip()

        if any(potential_sentence.endswith(abbrev) for abbrev in abbreviations):
            pos = end_pos
            continue
        else:
            remaining_text = target_text[end_pos:].lstrip()
            return potential_sentence, remaining_text
    return None, target_text
