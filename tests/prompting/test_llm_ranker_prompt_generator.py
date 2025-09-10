import pytest

from aipg.prompting.prompt_generator import LLMRankerPromptGenerator
from aipg.prompting.utils import parse_llm_ranker_scores


@pytest.mark.unit
def test_llm_ranker_prompt_generator_initialization() -> None:
    """Test that LLMRankerPromptGenerator initializes correctly."""
    topic = "machine learning"
    candidates = ["neural networks", "deep learning", "algorithms"]

    generator = LLMRankerPromptGenerator(topic=topic, candidates=candidates)

    assert generator.topic == topic
    assert generator.candidates == candidates
    assert generator.parser == parse_llm_ranker_scores


@pytest.mark.unit
@pytest.mark.parametrize(
    "topic,candidates,expected_prompt_contains",
    [
        (
            "machine learning",
            ["neural networks", "deep learning"],
            [
                "[Проблема студента]: machine learning",
                "1. neural networks",
                "2. deep learning",
            ],
        ),
        (
            "data structures",
            ["arrays", "linked lists", "trees", "graphs"],
            [
                "[Проблема студента]: data structures",
                "1. arrays",
                "2. linked lists",
                "3. trees",
                "4. graphs",
            ],
        ),
        (
            "single candidate",
            ["only one"],
            ["[Проблема студента]: single candidate", "1. only one"],
        ),
    ],
)
def test_llm_ranker_prompt_generator_generate_prompt(
    topic: str, candidates: list[str], expected_prompt_contains: list[str]
) -> None:
    """Test that generate_prompt creates correct prompt format."""
    generator = LLMRankerPromptGenerator(topic=topic, candidates=candidates)

    prompt = generator.generate_prompt()

    for expected_text in expected_prompt_contains:
        assert expected_text in prompt


@pytest.mark.unit
def test_llm_ranker_prompt_generator_generate_chat_prompt() -> None:
    """Test that generate_chat_prompt creates correct chat format."""
    generator = LLMRankerPromptGenerator(
        topic="test query", candidates=["candidate1", "candidate2"]
    )

    chat_prompt = generator.generate_chat_prompt()

    assert len(chat_prompt) == 2
    assert chat_prompt[0]["role"] == "system"
    assert "реранкера" in chat_prompt[0]["content"]
    assert chat_prompt[1]["role"] == "user"
    assert "[Проблема студента]: test query" in chat_prompt[1]["content"]
    assert "1. candidate1" in chat_prompt[1]["content"]
    assert "2. candidate2" in chat_prompt[1]["content"]


@pytest.mark.unit
def test_llm_ranker_prompt_generator_parser() -> None:
    """Test that the parser is correctly set."""
    generator = LLMRankerPromptGenerator(topic="test", candidates=["candidate"])

    assert generator.parser == parse_llm_ranker_scores
