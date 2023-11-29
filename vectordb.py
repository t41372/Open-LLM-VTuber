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
        self.collection = self.chroma_client.get_or_create_collection(
            name="talk_history"
        )

    def addMessage(
        self,
        message: str,
        speaker: str,
        date=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        verbose=True,
    ):
        """
        Save the input text it to the vector database.
        message: str
            the message to remember
        speaker: str
            the speaker of the message
        date: str
            the date of the message. default to today. Format: YYYY-MM-DD HH:MM:SS
        verbose: bool
            whether to print out the message
        """
        if verbose:
            print("Remembering message from {}: {}".format(speaker, message))

        self.collection.add(
            documents=[message],
            metadatas=[{"Speaker": speaker, "Date": date}],
            ids=str(datetime.now()),  # disreagrd ids for now
        )

    def queryMessage(self, query: str, verbose=False):
        """
        Query the vector database with the input query.
        query: str
            the query to search
        verbose: bool
            whether to print out the query
        return: dict, {"documents": documents(str list), "metadatas": metadatas(dict), "distances": distances(number list)}
            a dictionary containing a list of messages (str), a list of metadata (dict["Speaker", "Date"]]), and a list of distances (number) in vector space
            (documents, metadatas, distances)
        """
        if verbose:
            print("Querying message: {}".format(query))

        # Query the database
        results = self.collection.query(
            query_texts=query,
            n_results=5,
        )

        # Print out the results
        if verbose:
            print("Query result:")
            for result in results:
                print(result)

        # add [0] because for some reason, there is an extra layer of list
        # wrapping both of them, like this [[documents], [metadatas], [distances]]]
        return {
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0],
        }
