import pytest

from typing import List, Optional

from aipg.rag.ports import EmbeddingPort, VectorStorePort, RetrievedItem
from aipg.rag.service import RagService
from aipg.state import Project, Topic2Project


class DummyEmbedder(EmbeddingPort):
    def __init__(self, vector: Optional[List[float]] = None) -> None:
        self.vector = vector or [1.0, 0.0, 0.0]

    def embedding_processor(self, texts: List[str]) -> List[List[float]]:
        return [self.vector for _ in texts]


class DummyVectorStore(VectorStorePort):
    def __init__(self, candidates: Optional[List[RetrievedItem]] = None) -> None:
        self._candidates = candidates or []
        self.add_calls: List[dict] = []

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict],
    ) -> None:
        # Record call for potential debugging; test assertions avoid relying on this.
        self.add_calls.append({"ids": ids, "embeddings": embeddings, "metadatas": metadatas})

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        return self._candidates[:k]


@pytest.mark.unit
@pytest.mark.parametrize(
    "candidates,scores,threshold,expected_topic2project",
    [
        # Retrieved path: best score above threshold -> return matching candidate
        (
            [
                RetrievedItem(topic="t1", micro_project=Project(raw_markdown="mp1", topic="t1", goal="goal1", description="description1", input_data="input_data1", expected_output="expected_output1", expert_solution="expert_solution1", autotest="autotest1")),
                RetrievedItem(topic="t2", micro_project=Project(raw_markdown="mp2", topic="t2", goal="goal2", description="description2", input_data="input_data2", expected_output="expected_output2", expert_solution="expert_solution2", autotest="autotest2")),
            ],
            [0.2, 0.95],
            0.7,
            Topic2Project(topic="t2", project=Project(raw_markdown="mp2", topic="t2", goal="goal2", description="description2", input_data="input_data2", expected_output="expected_output2", expert_solution="expert_solution2", autotest="autotest2")),
        ),
        # Generated path: candidates exist but scores below threshold
        (
            [
                RetrievedItem(topic="a", micro_project=Project(raw_markdown="A", topic="a", goal="goalA", description="descriptionA", input_data="input_dataA", expected_output="expected_outputA", expert_solution="expert_solutionA", autotest="autotestA")),
                RetrievedItem(topic="b", micro_project=Project(raw_markdown="B", topic="b", goal="goalB", description="descriptionB", input_data="input_dataB", expected_output="expected_outputB", expert_solution="expert_solutionB", autotest="autotestB")),
            ],
            [0.1, 0.2],
            0.8,
            None
        ),
        # Generated path: no candidates
        (
            [],
            [],
            0.7,
            None
        ),
    ],
)
def test_try_to_get_main_paths(
    candidates: List[RetrievedItem],
    scores: List[float],
    threshold: float,
    expected_topic2project: Topic2Project
) -> None:
    topic = "my-topic"

    embedder = DummyEmbedder()
    vector_store = DummyVectorStore(candidates=candidates)

    def ranker(_query: str, _cands: List[str]) -> List[float]:
        return list(scores)

    service = RagService(
        embedder=embedder,
        vector_store=vector_store,
        similarity_threshold=threshold,
        k_candidates=5,
        ranker=ranker,
    )

    result = service.try_to_get(topic)

    if expected_topic2project is None:
        assert result is None
    else:
        assert result is not None
        assert result.topic == expected_topic2project.topic
        assert result.project == expected_topic2project.project


@pytest.mark.unit
def test_try_to_get_raises_without_ranker_when_candidates_present() -> None:
    embedder = DummyEmbedder()
    vector_store = DummyVectorStore(
        candidates=[RetrievedItem(topic="t", micro_project=Project(raw_markdown="mp", topic="t", goal="goal", description="description", input_data="input_data", expected_output="expected_output", expert_solution="expert_solution", autotest="autotest"))]
    )

    service = RagService(
        embedder=embedder,
        vector_store=vector_store,
        similarity_threshold=0.5,
        k_candidates=3,
        ranker=None,
    )

    with pytest.raises(RuntimeError):
        service.try_to_get("topic")

