from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort


class SourceEnum(Enum):
    RETRIEVED = 1
    GENERATED = 2


@dataclass
class RagResult:
    micro_project: str
    source: SourceEnum
    matched_topic: Optional[str]


class RagService:
    def __init__(
        self,
        embedder: EmbeddingPort,
        vector_store: VectorStorePort,
        similarity_threshold: float = 0.7,
        k_candidates: int = 5,
        ranker: Optional[Callable[[str, List[str]], List[float]]] = None,
        generator: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold
        self.k_candidates = k_candidates
        self.ranker = ranker
        self.generator = generator

    def get_or_create_micro_project(self, topic: str) -> RagResult:
        topic_embedding = self.embedder.embedding_processor([topic])[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=topic_embedding, k=self.k_candidates
        )
        topic_candidates = [candidate.topic for candidate in candidates]
        if topic_candidates:
            if self.ranker is None:
                raise RuntimeError("ranker is not configured")
            scores = self.ranker(topic, topic_candidates)
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            best_score = scores[best_idx]
            if best_score >= self.similarity_threshold:
                best_item = candidates[best_idx]
                return RagResult(
                    micro_project=best_item.micro_project,
                    source=SourceEnum.RETRIEVED,
                    matched_topic=best_item.topic,
                )
        if self.generator is None:
            raise RuntimeError("generator is not configured")
        micro_project = self.generator(topic)

        new_embedding = topic_embedding
        self.vector_store.add(
            ids=[topic],
            embeddings=[new_embedding],
            metadatas=[{"topic": topic, "micro_project": micro_project}],
        )
        return RagResult(
            micro_project=micro_project,
            source=SourceEnum.GENERATED,
            matched_topic=topic,
        )

    def retrieve(self, topic: str) -> Optional[str]:
        topic_embedding = self.embedder.embedding_processor([topic])[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=topic_embedding, k=self.k_candidates
        )
        candidate_topic = [c.topic for c in candidates]
        if not candidate_topic:
            return None
        if self.ranker is None:
            raise RuntimeError("Ranker is not configured")
        if self.generator is None:
            raise RuntimeError("Generator is not configured")
        scores = self.ranker(topic, candidate_topic)
        if not scores:
            return None
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        best_score = scores[best_idx]
        if best_score >= self.similarity_threshold:
            return candidates[best_idx].micro_project
        return None

    def save(self, topic: str, micro_project: str) -> None:
        topic_embedding = self.embedder.embedding_processor([topic])[0]
        self.vector_store.add(
            ids=[topic],
            embeddings=[topic_embedding],
            metadatas=[{"topic": topic, "micro_project": micro_project}],
        )
