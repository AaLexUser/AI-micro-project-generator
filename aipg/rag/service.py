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
        Try to retrieve a micro project for the given topic.
        Returns Topic2Project if found, None if not found.
        """
        embeddings = self.embedder.embedding_processor([topic])
        if not embeddings:
            raise RuntimeError(f"Failed to generate embedding for topic: '{topic}'")
        topic_embedding = embeddings[0]
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
        embeddings = self.embedder.embedding_processor([topic])
        if not embeddings:
            raise RuntimeError(f"Failed to generate embedding for topic: '{topic}'")
        topic_embedding = embeddings[0]
        self.vector_store.add(
            ids=[topic],
            embeddings=[topic_embedding],
            metadatas=[{"topic": topic, "micro_project": micro_project}],
        )
