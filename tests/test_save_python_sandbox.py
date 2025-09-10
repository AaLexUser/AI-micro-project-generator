import pytest

from sandbox.domain import SandboxSpec, InvalidSandboxInput
from sandbox.use_cases import save_python_sandbox


class DummySaver:
    def __init__(self, expected_ref: str):
        self.expected_ref = expected_ref

    def save(self, spec: SandboxSpec) -> str:  # adapter implementation mocked
        return self.expected_ref


@pytest.mark.parametrize(
    "python_version, requirements_txt",
    [
        ("3.10", None),
        ("3.11", "requests==2.32.3\npytest==8.3.3"),
    ],
)
def test_save_python_sandbox_success(python_version, requirements_txt):
    spec = SandboxSpec(python_version=python_version, requirements_txt=requirements_txt)
    expected_ref = "sandbox:abc123"
    saver = DummySaver(expected_ref)

    result = save_python_sandbox(spec, saver)

    assert isinstance(result, str)
    assert result == expected_ref


@pytest.mark.parametrize("bad_version", [None, "", 0])
def test_save_python_sandbox_invalid_input_raises(bad_version):
    spec = SandboxSpec(python_version=bad_version, requirements_txt=None)  # type: ignore[arg-type]
    saver = DummySaver("unused")

    with pytest.raises(InvalidSandboxInput):
        save_python_sandbox(spec, saver)

