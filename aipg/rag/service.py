from typing import Callable, List, Optional

from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort
from aipg.state import Project, Topic2Project


class RagService:
    def __init__(
        self,
        embedder: EmbeddingPort,
        vector_store: VectorStorePort,
        similarity_threshold: float = 0.7,
        k_candidates: int = 5,
        ranker: Optional[Callable[[str, List[str]], List[float]]] = None,
    ) -> None:
        """
        Initialize the RagService.
        
        Parameters:
            similarity_threshold (float): Minimum acceptable similarity score in [0, 1] required to accept a retrieved candidate.
            k_candidates (int): Number of nearest neighbors to request from the vector store when querying.
            ranker (Optional[Callable[[str, List[str]], List[float]]]): Optional ranking function that takes the query topic and a list of candidate topic strings and returns a list of scores (one per candidate). Required at retrieval time if any candidates are returned.
        
        Raises:
            ValueError: If `similarity_threshold` is not in [0, 1] or if `k_candidates` is not positive.
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold
        self.k_candidates = k_candidates
        self.ranker = ranker
        
        if similarity_threshold < 0 or similarity_threshold > 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if k_candidates <= 0:
            raise ValueError("k_candidates must be positive")

    def try_to_get(self, topic: str) -> Optional[Topic2Project]:
        """
        Attempt to find a matching Topic2Project for the given topic using embeddings and candidate ranking.
        
        Generates an embedding for `topic`, queries the vector store for up to `k_candidates` nearest entries, and—if any candidates are returned—requires a configured ranker to score those candidate topics. The highest-scoring candidate is returned as a Topic2Project when its score is >= the service's similarity_threshold; otherwise the method returns None.
        
        Raises:
            RuntimeError: If the vector store returns one or more candidates but no ranker is configured.
        
        Returns:
            Optional[Topic2Project]: The best-matching Topic2Project when a candidate meets the similarity threshold, or None if no suitable match is found.
        """
        topic_embedding = self.embedder.embedding_processor([topic])[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=topic_embedding, k=self.k_candidates
        )
        topic_candidates = [candidate.topic for candidate in candidates]
        if topic_candidates:
            if self.ranker is None:
                raise RuntimeError(
                    f"Ranker is required when candidates are found, but none was configured. "
                    f"Found {len(topic_candidates)} candidates for topic '{topic}'"
                )
            scores = self.ranker(topic, topic_candidates)
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            best_score = scores[best_idx]
            if best_score >= self.similarity_threshold:
                best_item = candidates[best_idx]
                return Topic2Project(topic=best_item.topic, project=best_item.micro_project)
        return None

    def save(self, topic: str, micro_project: Project) -> None:
        """
        Save a topic → micro-project mapping in the vector store using the topic's embedding.
        
        Computes an embedding for the provided topic and indexes it into the configured vector store. The stored entry uses the topic string as the id and includes metadata containing the original topic and the associated micro_project object.
        
        Parameters:
            topic (str): The topic text to embed and index.
            micro_project (Project): The micro-project to associate with the topic; stored verbatim in the entry metadata.
        """
        topic_embedding = self.embedder.embedding_processor([topic])[0]
        self.vector_store.add(
            ids=[topic],
            embeddings=[topic_embedding],
            metadatas=[{"topic": topic, "micro_project": micro_project}],
        )
