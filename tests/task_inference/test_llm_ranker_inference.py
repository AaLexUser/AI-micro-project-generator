from unittest.mock import AsyncMock

import pytest

from aipg.exceptions import OutputParserException
from aipg.state import ProcessTopicAgentState, Topic2Project
from aipg.task_inference.task_inference import LLMRankerInference


@pytest.mark.unit
@pytest.mark.parametrize(
    "topic,candidates,llm_responses,expected_best_candidate_idx,similarity_threshold",
    [
        # Successful ranking on first attempt - best candidate above threshold
        (
            "machine learning",
            ["neural networks", "deep learning"],
            ["[0.8, 0.9]"],
            1,  # Index of best candidate (0.9)
            0.7,
        ),
        # Successful ranking after retry - best candidate above threshold
        (
            "data structures",
            ["arrays", "linked lists", "trees"],
            ["invalid response", "[0.7, 0.6, 0.8]"],
            2,  # Index of best candidate (0.8)
            0.7,
        ),
        # Single candidate above threshold
        ("single topic", ["only candidate"], ["[0.95]"], 0, 0.7),
        # Best candidate below threshold - should return None
        ("low similarity", ["candidate1", "candidate2"], ["[0.5, 0.6]"], None, 0.7),
    ],
)
@pytest.mark.asyncio
async def test_llm_ranker_inference_success(
    topic: str,
    candidates: list[str],
    llm_responses: list[str],
    expected_best_candidate_idx: int | None,
    similarity_threshold: float,
) -> None:
    """Test that LLMRankerInference successfully ranks candidates and selects best one."""
    mock_llm = AsyncMock()
    mock_llm.query.side_effect = llm_responses

    # Create Topic2Project objects for candidates
    topic2project_candidates = [
        Topic2Project(topic=candidate) for candidate in candidates
    ]
    state = ProcessTopicAgentState(topic=topic, candidates=topic2project_candidates)
    inference = LLMRankerInference(
        llm=mock_llm, similarity_threshold=similarity_threshold
    )

    result = await inference.transform(state)

    assert result.candidates == topic2project_candidates

    if expected_best_candidate_idx is not None:
        assert result.topic == candidates[expected_best_candidate_idx]
        assert (
            result.project
            == topic2project_candidates[expected_best_candidate_idx].project
        )
    else:
        assert result.topic == topic
        assert result.project is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_ranker_inference_wrong_number_of_scores() -> None:
    """Test that LLMRankerInference handles wrong number of scores correctly."""
    mock_llm = AsyncMock()
    mock_llm.query.side_effect = [
        "[0.8, 0.9, 0.7]",  # 3 scores for 2 candidates
        "[0.8, 0.9]",  # Correct number of scores
    ]

    candidates = [Topic2Project(topic="candidate1"), Topic2Project(topic="candidate2")]
    state = ProcessTopicAgentState(topic="test query", candidates=candidates)
    inference = LLMRankerInference(llm=mock_llm, similarity_threshold=0.7)

    result = await inference.transform(state)

    assert result.topic == "candidate2"
    assert result.project == candidates[1].project
    assert mock_llm.query.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_ranker_inference_max_retries_exceeded() -> None:
    """Test that LLMRankerInference raises exception after max retries."""
    mock_llm = AsyncMock()
    mock_llm.query.return_value = "invalid response"

    candidates = [Topic2Project(topic="candidate1"), Topic2Project(topic="candidate2")]
    state = ProcessTopicAgentState(topic="test query", candidates=candidates)
    inference = LLMRankerInference(llm=mock_llm, similarity_threshold=0.7)

    with pytest.raises(OutputParserException):
        await inference.transform(state)

    # Should have tried 3 times
    assert mock_llm.query.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_ranker_inference_empty_candidates() -> None:
    """Test that LLMRankerInference handles empty candidates list."""
    mock_llm = AsyncMock()
    mock_llm.query.return_value = "[]"

    state = ProcessTopicAgentState(topic="test query", candidates=[])
    inference = LLMRankerInference(llm=mock_llm, similarity_threshold=0.7)

    result = await inference.transform(state)

    assert result.project is None
    assert result.topic == "test query"
    assert result.candidates == []
