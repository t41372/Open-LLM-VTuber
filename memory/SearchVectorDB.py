from threading import Lock

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class SearchVectorDB:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        # Thread-safe singleton pattern
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SearchVectorDB, cls).__new__(cls)
        return cls._instance

    def __init__(self, dimension=384, model_name='all-MiniLM-L6-v2'):
        if not hasattr(self, "_initialized"):
            # Initialize FAISS index and embedding model
            self.dimension = dimension
            self.index = faiss.IndexFlatL2(dimension)  # L2 distance metric
            self.model = SentenceTransformer(model_name)
            self._initialized = True

    def add_to_index(self, texts):
        """
        Add text embeddings to the FAISS index.

        Args:
            texts (List[str]): List of texts to encode and add to the index.
        """
        embeddings = self.model.encode(texts).astype('float16')
        self.index.add(embeddings)

    def semantic_search(self, question: str, top_k: int = 3):
        """
        Perform semantic search using text-based queries.

        Args:
            question (str): User's question.
            top_k (int): Number of top results to retrieve.

        Returns:
            List[dict]: Retrieved results with scores and indices.
        """
        # Encode the question into an embedding
        query_embedding = self.model.encode([question]).astype('float16')

        # Perform the search
        return self.vector_search(query_embedding[0], top_k)

    def vector_search(self, vector: np.ndarray, top_k: int = 3):
        """
        Perform vector-based search.

        Args:
            vector (np.ndarray): Embedding vector for search.
            top_k (int): Number of top results to retrieve.

        Returns:
            List[dict]: Retrieved results with scores and indices.
        """
        # Perform the search
        distances, indices = self.index.search(np.array([vector], dtype='float16'), top_k)

        # Format and return the results
        output = []
        for i in range(len(indices[0])):
            output.append({
                "index": indices[0][i],
                "distance": distances[0][i]
            })
        return output
