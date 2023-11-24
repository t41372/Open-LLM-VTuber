import traceback


def validate_text(text):    
    '''
    Validate text input to make sure it's a string and not empty.
    text: str
        the text to validate
    return: bool
        True if the text is valid. False otherwise.
    '''
    if not isinstance(text, str) or text.strip() == "":
        print("The text cannot be empty or non-string.")
        print("Received type: {} and value: {}".format(type(text), text))
        traceback.print_stack()  # Print the trace stack
        return False
    else:
        return True

# this fuction has become obsolete due to changes in the LLM template
def removeBadPrefix(str, badPrefixList=["Me:", "AI:", "Unhelpful AI:"]):
    '''
    remove bad prefix of the string
    str: str
        the string to remove the bad prefix from
    badPrefixList: list of str
        the list of bad prefix strings to remove. Default: ["Me:", "AI:", "Unhelpful AI:"]
    return: str
        the string with the bad start removed
    '''
    badPrefixList = ["Me:", "AI:", "Unhelpful AI:"]
    index = 0
    while index < len(badPrefixList):
        if str.startswith(badPrefixList[index]):
            print("\n\n>> Removing " + badPrefixList[index] + " from the beginning of the response.\n")
            str = str[len(badPrefixList[index]):].strip()
            index = 0 # reset index and run it again in case of multiple badStarts
        else:
            # print("\n>> " + badPrefixList[index] + " not found at the beginning of the response.")
            index += 1
    return str