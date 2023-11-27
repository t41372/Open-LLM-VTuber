
from datetime import datetime
import chromadb
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .

class VectorDB:



    def __init__(self, MEMORY_DB_PATH=os.getenv("MEMORY_DB_PATH")):
        self.MEMORY_DB_PATH = MEMORY_DB_PATH
        # Initialize chromadb client
        self.chroma_client = chromadb.PersistentClient(path=MEMORY_DB_PATH)
        # collection = chroma_client.create_collection(name="my_collection")
        self.collection = self.chroma_client.get_or_create_collection(name="talk_history")


    def addMessage(self, message, speaker, verbose=True):
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
        
        self.collection.add(
            documents=[message],
            metadatas=[{"Speaker": speaker, "Timestamp": str(datetime.now())}],
            ids=str(datetime.now()) # disreagrd ids for now
        )
        

    def queryMessage(self, query, verbose=False):
        '''
        Query the vector database with the input query.
        query: str
            the query to search
        verbose: bool
            whether to print out the query
        return: tuple of list of str, list of dict
            the list of messages (str) and the list of metadata (dict["Speaker", "Timestamp"]])
            (documents, metadatas)
        '''
        if verbose:
            print("Querying message: {}".format(query))
        
        # Query the database
        results = self.collection.query(
            query_texts=query,
            n_results=10,
        )

        # Print out the results
        if verbose:
            print("Query result:")
            for result in results:
                print(result)
        
        return (results["documents"], results["metadatas"])


