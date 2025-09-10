import pytest

from aipg.exceptions import OutputParserException
from aipg.prompting.utils import parse_llm_ranker_scores


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_text,expected_scores",
    [
        # Valid JSON array
        ("[0.8, 0.2, 0.9]", [0.8, 0.2, 0.9]),
        ("[0.0, 1.0, 0.5]", [0.0, 1.0, 0.5]),
        ("[0.85]", [0.85]),
        ("[]", []),
        # JSON with fenced code block
        ("```json\n[0.7, 0.3]\n```", [0.7, 0.3]),
        ("```\n[0.6, 0.4, 0.8]\n```", [0.6, 0.4, 0.8]),
        # JSON with extra text
        ("Here are the scores: [0.9, 0.1]", [0.9, 0.1]),
        # Integer values (should be converted to float)
        ("[1, 0, 0.5]", [1.0, 0.0, 0.5]),
    ],
)
def test_parse_llm_ranker_scores_valid_inputs(
    input_text: str, expected_scores: list[float]
) -> None:
    """Test that valid inputs are parsed correctly."""
    result = parse_llm_ranker_scores(input_text)
    assert result == expected_scores


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_text,expected_exception_type",
    [
        # Invalid JSON
        ("not json", OutputParserException),
        ("{invalid json}", OutputParserException),
        # Wrong data type - no valid array to extract
        ('{"scores": "not an array"}', OutputParserException),
        ("0.8", OutputParserException),
        # Out of range values
        ("[1.1, 0.5]", OutputParserException),
        ("[-0.1, 0.5]", OutputParserException),
        ("[0.8, 2.0]", OutputParserException),
        # Invalid values
        ("[0.8, 'invalid', 0.5]", OutputParserException),
        ("[0.8, null, 0.5]", OutputParserException),
        # Empty input
        ("", list),
        ("   ", list),
    ],
)
def test_parse_llm_ranker_scores_invalid_inputs(
    input_text: str, expected_exception_type: type
) -> None:
    """Test that invalid inputs raise appropriate exceptions."""
    if expected_exception_type is list:
        # Special case for empty input
        result = parse_llm_ranker_scores(input_text)
        assert result == []
    else:
        with pytest.raises(expected_exception_type):
            parse_llm_ranker_scores(input_text)
