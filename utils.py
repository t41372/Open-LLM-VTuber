import traceback
import os


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



def messageLogger(message, chatHistoryDir, filename):
    '''
    Log the message to a chat history file.
    message: str
        the message to log
    chatHistoryDir: str
        the directory to save the chat history.
    filename: str
        the name of the file to save the chat history.
    '''
    # print("Logging message...")
    try:
        if not os.path.isdir(chatHistoryDir):
            os.makedirs(chatHistoryDir)
        
        filepath = os.path.join(chatHistoryDir, filename)
        
        with open(filepath, 'a') as file:
            file.write(f"{message}\n")
        # print("Message logged successfully.")
    except Exception as e:
        print("Failed to log message:", str(e))
        # print("message: {} \n chatHistoryDir: {} \n filename: {}".format(message, chatHistoryDir, filename))


def backUpFile(targetFilePath, verbose=True):
    '''
    Back up the file by creating a copy of it. 
    Backup file will be named as the original file with .bk extension.
    targetFilePath: str
        the path to the file to be backup.
    return: str
        the path to the backup file
    '''
    
    # Get the directory and filename from the memory_db_path
    directory, filename = os.path.split(targetFilePath)
    
    # Create the backup file path
    backup_path = os.path.join(directory, f"{filename}.bk")
    
    # Copy the memory database file to the backup file path
    os.system("cp -r {} {}".format(targetFilePath, backup_path))

    if verbose:
        print("Backup file created at: {}".format(backup_path))
    
    return backup_path

def restoreFile(targetFilePath, backupFilePath, verbose=True):
    '''
    Restore the file by replacing the target file with the backup file.
    targetFilePath: str
        the path to the file to be replaced by backup.
    backupFilePath: str
        the path to the backup file.
    return: str
        the path to the target file
    '''
    os.system("cp -r {} {}".format(backupFilePath, targetFilePath))
    
    # Remove the backup file
    os.system("rm -r {}".format(backupFilePath))

    if verbose:
        print("File restored at: {}".format(targetFilePath))
    
    return targetFilePath





