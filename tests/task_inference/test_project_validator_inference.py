from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from aipg.exceptions import OutputParserException
from aipg.state import ProcessTopicAgentState, Project, ProjectValidationResult
from aipg.task_inference.task_inference import ProjectValidatorInference


def create_project(
    topic: str, project_data: dict[str, Any] | None = None
) -> Project:
    """Factory function to create Project objects for testing."""
    default_project_data = {
        "raw_markdown": f"# {topic}\n\nDescription: Test project for {topic}",
        "topic": topic,
        "goal": f"goal_{topic}",
        "description": f"description_{topic}",
        "input_data": f"input_data_{topic}",
        "expected_output": f"expected_output_{topic}",
        "expert_solution": f"expert_solution_{topic}",
        "autotest": f"autotest_{topic}",
    }
    
    if project_data is not None:
        default_project_data.update(project_data)

    return Project(**default_project_data)


@pytest.mark.unit
@pytest.mark.parametrize(
    "project_markdown,llm_responses,expected_validation_result",
    [
        # Successful validation on first attempt
        (
            "# Test Project\n\nDescription: Test project",
            [
                """is_valid: true
checks:
  - rule_id: "SOLVABILITY"
    passed: true
    comment: "OK"
  - rule_id: "AUTOTEST_SCOPE"
    passed: true
    comment: "OK"
"""
            ],
            {
                "is_valid": True,
                "checks": [
                    {"rule_id": "SOLVABILITY", "passed": True, "comment": "OK"},
                    {"rule_id": "AUTOTEST_SCOPE", "passed": True, "comment": "OK"},
                ],
            },
        ),
        # Successful validation after retry
        (
            "# Another Project\n\nDescription: Another test project",
            [
                "invalid response",
                """is_valid: false
checks:
  - rule_id: "SOLVABILITY"
    passed: false
    comment: "Missing required data in input"
  - rule_id: "AUTOTEST_SCOPE"
    passed: true
    comment: "OK"
""",
            ],
            {
                "is_valid": False,
                "checks": [
                    {"rule_id": "SOLVABILITY", "passed": False, "comment": "Missing required data in input"},
                    {"rule_id": "AUTOTEST_SCOPE", "passed": True, "comment": "OK"},
                ],
            },
        ),
        # Validation with no autotest
        (
            "# Project Without Autotest\n\nDescription: Project without autotest",
            [
                """is_valid: true
checks:
  - rule_id: "SOLVABILITY"
    passed: true
    comment: "OK"
  - rule_id: "AUTOTEST_SCOPE"
    passed: true
    comment: "No autotest provided"
"""
            ],
            {
                "is_valid": True,
                "checks": [
                    {"rule_id": "SOLVABILITY", "passed": True, "comment": "OK"},
                    {"rule_id": "AUTOTEST_SCOPE", "passed": True, "comment": "No autotest provided"},
                ],
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_project_validator_inference_success(
    project_markdown: str,
    llm_responses: list[str],
    expected_validation_result: dict,
) -> None:
    """Test that ProjectValidatorInference successfully validates projects."""
    mock_llm = AsyncMock()
    mock_llm.query.side_effect = llm_responses

    # Create a Project object using the factory
    project = create_project(
        topic="test topic",
        project_data={"raw_markdown": project_markdown}
    )
    
    state = ProcessTopicAgentState(topic="test topic", project=project)
    inference = ProjectValidatorInference(llm=mock_llm)

    result = await inference.transform(state)

    assert result.project is not None
    assert result.project.raw_markdown == project_markdown
    # Ensure validation_result is set after successful transformation
    assert result.validation_result is not None
    validation_result = cast(ProjectValidationResult, result.validation_result)
    # Compare the validation result object attributes
    assert validation_result.is_valid == expected_validation_result["is_valid"]
    assert len(validation_result.checks) == len(expected_validation_result["checks"])
    for i, expected_check in enumerate(expected_validation_result["checks"]):
        assert validation_result.checks[i].rule_id == expected_check["rule_id"]
        assert validation_result.checks[i].passed == expected_check["passed"]
        assert validation_result.checks[i].comment == expected_check["comment"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_project_validator_inference_max_retries_exceeded() -> None:
    """Test that ProjectValidatorInference raises exception after max retries."""
    mock_llm = AsyncMock()
    mock_llm.query.return_value = "invalid response"

    project = create_project(topic="test topic")
    
    state = ProcessTopicAgentState(topic="test topic", project=project)
    inference = ProjectValidatorInference(llm=mock_llm)

    with pytest.raises(OutputParserException):
        await inference.transform(state)

    # Should have tried 3 times
    assert mock_llm.query.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_project_validator_inference_yaml_code_block() -> None:
    """Test that ProjectValidatorInference handles YAML code blocks correctly."""
    mock_llm = AsyncMock()
    mock_llm.query.return_value = """```yaml
is_valid: true
checks:
  - rule_id: "SOLVABILITY"
    passed: true
    comment: "OK"
  - rule_id: "AUTOTEST_SCOPE"
    passed: true
    comment: "OK"
```"""

    project = create_project(topic="test topic")
    
    state = ProcessTopicAgentState(topic="test topic", project=project)
    inference = ProjectValidatorInference(llm=mock_llm)

    result = await inference.transform(state)

    expected_checks: list[dict[str, Any]] = [
        {"rule_id": "SOLVABILITY", "passed": True, "comment": "OK"},
        {"rule_id": "AUTOTEST_SCOPE", "passed": True, "comment": "OK"},
    ]
    # Ensure validation_result is set after successful transformation
    assert result.validation_result is not None
    validation_result = cast(ProjectValidationResult, result.validation_result)
    # Compare the validation result object attributes
    assert validation_result.is_valid is True
    assert len(validation_result.checks) == len(expected_checks)
    for i, expected_check in enumerate(expected_checks):
        assert validation_result.checks[i].rule_id == expected_check["rule_id"]
        assert validation_result.checks[i].passed == expected_check["passed"]
        assert validation_result.checks[i].comment == expected_check["comment"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_project_validator_inference_empty_response() -> None:
    """Test that ProjectValidatorInference handles empty response correctly."""
    mock_llm = AsyncMock()
    mock_llm.query.return_value = ""

    project = create_project(topic="test topic")
    
    state = ProcessTopicAgentState(topic="test topic", project=project)
    inference = ProjectValidatorInference(llm=mock_llm)

    with pytest.raises(OutputParserException):
        await inference.transform(state)

    # Should have tried 3 times
    assert mock_llm.query.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_project_validator_inference_no_project() -> None:
    """Test that ProjectValidatorInference handles state with no project correctly."""
    mock_llm = AsyncMock()
    
    state = ProcessTopicAgentState(topic="test topic", project=None)
    inference = ProjectValidatorInference(llm=mock_llm)

    result = await inference.transform(state)

    # Should return the state unchanged when no project is available
    assert result.project is None
    assert result.validation_result is None
    # Should not have called the LLM
    assert mock_llm.query.call_count == 0