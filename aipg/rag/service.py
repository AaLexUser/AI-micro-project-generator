from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from .ports import EmbeddingPort, VectorStorePort, RetrievedItem


@dataclass
class RagResult:
    micro_project: str
    source: str  # "retrieved" or "generated"
    matched_issue: Optional[str] = None


class RagService:
    def __init__(
        self,
        embedder: EmbeddingPort,
        vector_store: VectorStorePort,
        ranker: Callable[[str, List[str]], List[float]],
        generator: Callable[[str], str],
        similarity_threshold: float = 0.7,
        k_candidates: int = 5,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.ranker = ranker
        self.generator = generator
        self.similarity_threshold = similarity_threshold
        self.k_candidates = k_candidates

    def get_or_create_micro_project(self, issue: str) -> RagResult:
        issue_embedding = self.embedder.embed([issue])[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=issue_embedding, k=self.k_candidates
        )

        candidate_issues = [c.issue for c in candidates]
        if candidate_issues:
            scores = self.ranker(issue, candidate_issues)
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            best_score = scores[best_idx]
            if best_score >= self.similarity_threshold:
                best_item = candidates[best_idx]
                return RagResult(
                    micro_project=best_item.micro_project,
                    source="retrieved",
                    matched_issue=best_item.issue,
                )

        # Generate new micro-project
        micro_project = self.generator(issue)
        # Save to vector store
        new_embedding = issue_embedding  # reuse computed embedding
        self.vector_store.add(
            ids=[issue],
            embeddings=[new_embedding],
            metadatas=[{"issue": issue, "micro_project": micro_project}],
        )
        return RagResult(micro_project=micro_project, source="generated")

    # Integration methods for external generation
    def retrieve(self, issue: str) -> Optional[str]:
        issue_embedding = self.embedder.embed([issue])[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=issue_embedding, k=self.k_candidates
        )
        candidate_issues = [c.issue for c in candidates]
        if not candidate_issues:
            return None
        scores = self.ranker(issue, candidate_issues)
        if not scores:
            return None
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        best_score = scores[best_idx]
        if best_score >= self.similarity_threshold:
            return candidates[best_idx].micro_project
        return None

    def save(self, issue: str, micro_project: str) -> None:
        issue_embedding = self.embedder.embed([issue])[0]
        self.vector_store.add(
            ids=[issue],
            embeddings=[issue_embedding],
            metadatas=[{"issue": issue, "micro_project": micro_project}],
        )

