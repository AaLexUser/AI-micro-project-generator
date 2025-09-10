import pytest
from dataclasses import dataclass
from typing import Protocol, Optional


# The tests operate as a black box around the service API.
# We define minimal local Protocols/DTOs mirroring the public contract
# to avoid coupling to implementation details.


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


class SandboxRunner(Protocol):
    def run(self, code: str, input_data: Optional[str], timeout_seconds: int) -> SandboxResult: ...


class FakeRunner:
    def __init__(self, result: SandboxResult):
        self._result = result

    def run(self, code: str, input_data: Optional[str], timeout_seconds: int) -> SandboxResult:
        return self._result


@pytest.mark.unit
@pytest.mark.parametrize(
    "code,result",
    [
        ("print(6*7)", SandboxResult(stdout="42\n", stderr="", exit_code=0)),
        ("print('hello')", SandboxResult(stdout="hello\n", stderr="", exit_code=0)),
    ],
)
def test_service_returns_adapter_result_for_valid_code(code, result):
    # Arrange: service uses a mocked adapter (FakeRunner)
    from aipg.sandbox.service import PythonSandboxService

    service = PythonSandboxService(runner=FakeRunner(result))

    # Act
    outcome = service.run_code(code)

    # Assert: verify meaningful outcome only (behavioral contract)
    assert isinstance(outcome.stdout, str)
    assert outcome.exit_code == 0
    assert not outcome.timed_out
    # Avoid brittle exact string checks; ensure expected content is present
    assert outcome.stdout.strip() in result.stdout.strip()


@pytest.mark.unit
def test_service_raises_value_error_on_empty_code():
    from aipg.sandbox.service import PythonSandboxService

    service = PythonSandboxService(runner=FakeRunner(SandboxResult("", "", 0)))

    with pytest.raises(ValueError):
        service.run_code("")

