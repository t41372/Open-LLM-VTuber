
import datetime
import chromadb
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .

MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH")


# Initialize chromadb client
chroma_client = chromadb.PersistentClient(path=MEMORY_DB_PATH)
# collection = chroma_client.create_collection(name="my_collection")
collection = chroma_client.get_or_create_collection(name="talk_history")


def rememberMessage(message, speaker, verbose=True):
    '''
    Save the input text it to the vector database.
    message: str
        the message to remember
    speaker: str
        the speaker of the message
    verbose: bool
        whether to print out the message
    '''
    if verbose:
        print("Remembering message from {}: {}".format(speaker, message))
    
    collection.add(
        documents=[message],
        metadatas=[{"Speaker": speaker, "Timestamp": str(datetime.now())}],
        # ids=["id1", "id2"] # disreagrd ids for now
    )
    

def queryMessage(query, verbose=True):
    '''
    Query the vector database with the input query.
    query: str
        the query to search
    verbose: bool
        whether to print out the query
    '''
    if verbose:
        print("Querying message: {}".format(query))
    
    # Query the database
    results = collection.query(
        query=query,
    )
    
    # Print out the results
    if verbose:
        print("Query result:")
        for result in results:
            print(result)
    
    return results


