import pytest

from aipg.exceptions import OutputParserException
from aipg.prompting.utils import parse_define_topics


@pytest.mark.parametrize(
    "raw_input, expected",
    [
        (
            # YAML fenced block with mapping
            (
                "```yaml\n"
                "topics:\n"
                '  - "SQL: Разница между INNER и LEFT JOIN"\n'
                '  - "Pandas: Агрегация с groupby"\n'
                "```\n"
            ),
            [
                "SQL: Разница между INNER и LEFT JOIN",
                "Pandas: Агрегация с groupby",
            ],
        ),
        (
            # Raw YAML mapping with empty list
            "topics: []",
            [],
        ),
        (
            # Plain YAML list (no mapping)
            (
                '- "SQL: Разница между INNER и LEFT JOIN"\n'
                '- "Pandas: Агрегация с groupby"\n'
            ),
            [
                "SQL: Разница между INNER и LEFT JOIN",
                "Pandas: Агрегация с groupby",
            ],
        ),
    ],
)
def test_parse_define_topics_success(raw_input: str, expected: list[str]):
    result = parse_define_topics(raw_input)
    assert isinstance(result, list)
    # Validate meaningful outcome: list of the expected topics
    assert result == expected


@pytest.mark.parametrize(
    "raw_input",
    [
        # Invalid YAML
        """```yaml\ntopics: [\n- a\n```""",
        # Unsupported root type (YAML scalar)
        '"just a string"',
        # 'topics' present but not a list
        "topics: {a: 1}",
    ],
)
def test_parse_define_topics_errors(raw_input: str):
    with pytest.raises(OutputParserException):
        parse_define_topics(raw_input)
