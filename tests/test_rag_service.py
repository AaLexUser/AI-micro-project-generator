from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

from aipg.rag.ports import RetrievedItem
from aipg.rag.service import RagService


class FakeEmbedder:
    def __init__(self, mapping: dict[str, List[float]]):
        self.mapping = mapping

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self.mapping[t] for t in texts]


class FakeVectorStore:
    def __init__(self, items: list[RetrievedItem] | None = None):
        self.items = items or []
        self.add_calls: list[dict] = []

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]):
        for meta in metadatas:
            self.items.append(
                RetrievedItem(
                    issue=meta["issue"], micro_project=meta["micro_project"], metadata=meta
                )
            )
        self.add_calls.append({"ids": ids, "embeddings": embeddings, "metadatas": metadatas})

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        return self.items[:k]


@pytest.mark.parametrize(
    "issue, existing, rank_scores, expect_source",
    [
        (
            "How to fix list index error?",
            [RetrievedItem(issue="IndexError in Python", micro_project="Fix index handling")],
            [0.9],
            "retrieved",
        ),
        (
            "How to fix list index error?",
            [RetrievedItem(issue="Null pointer in Java", micro_project="Handle nulls")],
            [0.3],
            "generated",
        ),
    ],
)
def test_rag_service_retrieve_or_generate(issue, existing, rank_scores, expect_source):
    embedder = FakeEmbedder({issue: [0.1, 0.2, 0.3]})
    store = FakeVectorStore(existing.copy())

    def ranker(q: str, cands: List[str]) -> List[float]:
        return rank_scores

    def generator(q: str) -> str:
        return "Generated Micro Project"

    service = RagService(
        embedder=embedder,
        vector_store=store,
        ranker=ranker,
        generator=generator,
        similarity_threshold=0.7,
        k_candidates=5,
    )

    result = service.get_or_create_micro_project(issue)

    assert result.source == expect_source
    if expect_source == "retrieved":
        assert result.micro_project == existing[0].micro_project
        assert result.matched_issue == existing[0].issue
        assert store.add_calls == []
    else:
        assert result.micro_project == "Generated Micro Project"
        assert result.matched_issue is None
        assert store.add_calls, "Generated project must be saved to vector store"

