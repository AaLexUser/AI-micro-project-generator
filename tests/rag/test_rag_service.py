from typing import Any, List, Optional

import pytest

from aipg.domain import Project, Topic2Project
from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort
from aipg.rag.service import RagService


def create_topic2project(
    topic: str, project_data: dict[str, Any] | None = None
) -> Topic2Project:
    """Factory function to create Topic2Project objects for testing."""
    if project_data is None:
        project_data = {
            "raw_markdown": f"mp_{topic}",
            "topic": topic,
            "goal": f"goal_{topic}",
            "description": f"description_{topic}",
            "input_data": f"input_data_{topic}",
            "expected_output": f"expected_output_{topic}",
            "expert_solution": f"expert_solution_{topic}",
            "autotest": f"autotest_{topic}",
        }

    project = Project(**project_data)
    return Topic2Project(topic=topic, project=project)


def create_retrieved_item(
    topic: str, project_data: dict[str, Any] | None = None
) -> RetrievedItem:
    """Factory function to create RetrievedItem objects for testing."""
    if project_data is None:
        project_data = {
            "raw_markdown": f"mp_{topic}",
            "topic": topic,
            "goal": f"goal_{topic}",
            "description": f"description_{topic}",
            "input_data": f"input_data_{topic}",
            "expected_output": f"expected_output_{topic}",
            "expert_solution": f"expert_solution_{topic}",
            "autotest": f"autotest_{topic}",
        }

    project = Project(**project_data)
    return RetrievedItem(topic=topic, micro_project=project)


class DummyEmbedder(EmbeddingPort):
    def __init__(
        self, vector: Optional[List[float]] = None, should_fail: bool = False
    ) -> None:
        self.vector = vector or [1.0, 0.0, 0.0]
        self.should_fail = should_fail

    async def embedding_processor(self, texts: List[str]) -> List[List[float]]:
        if self.should_fail:
            return []  # Simulate embedding service failure
        return [self.vector for _ in texts]


class DummyVectorStore(VectorStorePort):
    def __init__(self, candidates: Optional[List[RetrievedItem]] = None) -> None:
        self._candidates = candidates or []
        self.add_calls: List[dict] = []

    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict],
    ) -> None:
        # Record call for potential debugging; test assertions avoid relying on this.
        self.add_calls.append(
            {"ids": ids, "embeddings": embeddings, "metadatas": metadatas}
        )

    async def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        return self._candidates[:k]


@pytest.mark.unit
@pytest.mark.parametrize(
    "candidates,k_candidates,expected_topic2projects",
    [
        # Retrieved path: candidates found -> return all candidates as Topic2Project list
        (
            [create_retrieved_item("t1"), create_retrieved_item("t2")],
            5,  # k_candidates > available candidates
            [create_topic2project("t1"), create_topic2project("t2")],
        ),
        # k_candidates < available candidates -> limit results
        (
            [
                create_retrieved_item("t1"),
                create_retrieved_item("t2"),
                create_retrieved_item("t3"),
            ],
            2,  # k_candidates < available candidates
            [create_topic2project("t1"), create_topic2project("t2")],
        ),
        # No candidates found -> return empty list
        ([], 5, []),
    ],
)
@pytest.mark.asyncio
async def test_try_to_get_main_paths(
    candidates: List[RetrievedItem],
    k_candidates: int,
    expected_topic2projects: List[Topic2Project],
) -> None:
    topic = "my-topic"

    embedder = DummyEmbedder()
    vector_store = DummyVectorStore(candidates=candidates)

    service = RagService(
        embedder=embedder,
        vector_store=vector_store,
        k_candidates=k_candidates,
    )

    result = await service.try_to_get(topic)

    assert len(result) == len(expected_topic2projects)
    for i, expected in enumerate(expected_topic2projects):
        assert result[i].topic == expected.topic
        assert result[i].project == expected.project


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_to_get_raises_when_embedding_processor_fails() -> None:
    """Test that try_to_get raises RuntimeError when embedding processor returns empty list."""
    embedder = DummyEmbedder(should_fail=True)
    vector_store = DummyVectorStore()

    service = RagService(
        embedder=embedder,
        vector_store=vector_store,
        k_candidates=3,
    )

    with pytest.raises(
        RuntimeError, match="Failed to generate embedding for topic: 'test-topic'"
    ):
        await service.try_to_get("test-topic")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_raises_when_embedding_processor_fails() -> None:
    """Test that save raises RuntimeError when embedding processor returns empty list."""
    embedder = DummyEmbedder(should_fail=True)
    vector_store = DummyVectorStore()

    service = RagService(
        embedder=embedder,
        vector_store=vector_store,
        k_candidates=3,
    )

    test_project = Project(
        raw_markdown="test",
        topic="test-topic",
        goal="test goal",
        description="test description",
        input_data="test input",
        expected_output="test output",
        expert_solution="test solution",
        autotest="test autotest",
    )

    with pytest.raises(
        RuntimeError, match="Failed to generate embedding for topic: 'test-topic'"
    ):
        await service.save("test-topic", test_project)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_success() -> None:
    """Test that save works correctly when all conditions are met."""
    embedder = DummyEmbedder()
    vector_store = DummyVectorStore()

    service = RagService(
        embedder=embedder,
        vector_store=vector_store,
        k_candidates=3,
    )

    test_project = Project(
        raw_markdown="test content",
        topic="test-topic",
        goal="test goal",
        description="test description",
        input_data="test input",
        expected_output="test output",
        expert_solution="test solution",
        autotest="test autotest",
    )

    # Should not raise any exception
    await service.save("test-topic", test_project)

    # Verify that add was called on the vector store
    assert len(vector_store.add_calls) == 1
    call = vector_store.add_calls[0]
    assert len(call["ids"]) == 1
    assert len(call["embeddings"]) == 1
    assert len(call["metadatas"]) == 1
    assert call["metadatas"][0]["topic"] == "test-topic"
    assert call["metadatas"][0]["project_md"] == "test content"


@pytest.mark.unit
def test_constructor_raises_when_k_candidates_invalid() -> None:
    """Test that constructor raises ValueError when k_candidates is not positive."""
    embedder = DummyEmbedder()
    vector_store = DummyVectorStore()

    with pytest.raises(ValueError, match="k_candidates must be positive"):
        RagService(
            embedder=embedder,
            vector_store=vector_store,
            k_candidates=0,
        )

    with pytest.raises(ValueError, match="k_candidates must be positive"):
        RagService(
            embedder=embedder,
            vector_store=vector_store,
            k_candidates=-1,
        )
