from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from aipg.state import Project


@dataclass
class RetrievedItem:
    topic: str
    micro_project: Project
    metadata: Optional[dict] = None


@dataclass
class EmbeddingPort(ABC):
    @abstractmethod
    def embedding_processor(self, texts: List[str]) -> List[List[float]]: """
Convert a list of input texts into their corresponding numeric embeddings.

Given a list of strings, return a list of float vectors where each vector is the embedding for the input at the same index. Implementations must preserve input order and return one embedding per input; all embeddings in a single call are expected to have the same dimensionality.
"""
...


@dataclass
class VectorStorePort(ABC):
    @abstractmethod
    def add(
        self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]
    ) -> None:
        """
        Store a batch of embeddings in the vector store, associating each embedding with an identifier and optional metadata.
        
        Each list (ids, embeddings, metadatas) must have the same length; elements at the same index are associated together (ids[i] -> embeddings[i] -> metadatas[i]). Implementations should persist these entries so they become available for subsequent queries.
        
        Parameters:
            ids: Unique string identifiers for each embedding.
            embeddings: Embedding vectors; one list of floats per id.
            metadatas: Metadata dictionaries corresponding to each id.
        
        Returns:
            None
        """
        raise NotImplementedError()

    @abstractmethod
    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        """
        Return the top-k stored items most similar to the provided embedding.
        
        Parameters:
            embedding (List[float]): Query embedding vector.
            k (int): Number of nearest items to retrieve.
        
        Returns:
            List[RetrievedItem]: Retrieved items sorted by descending similarity (best match first). Implementations may return fewer than k items if the store contains fewer entries.
        """
        raise NotImplementedError
