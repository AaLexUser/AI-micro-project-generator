"""Tests for BugFixerPromptGenerator."""

from aipg.prompting.prompt_generator import BugFixerPromptGenerator
from aipg.sandbox.domain import SandboxResult


class TestBugFixerPromptGenerator:
    """Test cases for BugFixerPromptGenerator."""

    def test_initialization(self):
        """Test that BugFixerPromptGenerator initializes correctly."""
        project_markdown = "# Test Project\nSome content"
        sandbox_result = SandboxResult(
            stdout="Hello World",
            stderr="",
            exit_code=0,
            timed_out=False
        )
        
        generator = BugFixerPromptGenerator(project_markdown, sandbox_result)
        
        assert generator.project_markdown == project_markdown
        assert generator.sandbox_result == sandbox_result

    def test_generate_prompt(self):
        """Test that generate_prompt returns correctly formatted prompt."""
        project_markdown = "# Test Project\nSome content"
        sandbox_result = SandboxResult(
            stdout="Hello World",
            stderr="Error: something went wrong",
            exit_code=1,
            timed_out=True
        )
        
        generator = BugFixerPromptGenerator(project_markdown, sandbox_result)
        prompt = generator.generate_prompt()
        
        assert "[Микропроект для исправления]:" in prompt
        assert "[Результаты выполнения]:" in prompt
        assert project_markdown in prompt
        assert "Hello World" in prompt
        assert "Error: something went wrong" in prompt
        assert "exit_code: 1" in prompt
        assert "is_timed_out: True" in prompt

    def test_system_prompt_loaded(self):
        """Test that system prompt is loaded from bug_fixer.md file."""
        project_markdown = "# Test Project"
        sandbox_result = SandboxResult(stdout="", stderr="", exit_code=0)
        
        generator = BugFixerPromptGenerator(project_markdown, sandbox_result)
        system_prompt = generator.system_prompt
        
        # Check that the system prompt contains key elements from bug_fixer.md
        assert "ИИ-инженер по качеству" in system_prompt
        assert "анализировать и исправлять ошибки" in system_prompt
        assert "stderr" in system_prompt
        assert "exit_code" in system_prompt

    def test_chat_prompt_generation(self):
        """Test that generate_chat_prompt returns properly formatted chat messages."""
        project_markdown = "# Test Project"
        sandbox_result = SandboxResult(
            stdout="output",
            stderr="error",
            exit_code=1
        )
        
        generator = BugFixerPromptGenerator(project_markdown, sandbox_result)
        chat_prompt = generator.generate_chat_prompt()
        
        assert len(chat_prompt) == 2
        assert chat_prompt[0]["role"] == "system"
        assert chat_prompt[1]["role"] == "user"
        assert "ИИ-инженер по качеству" in chat_prompt[0]["content"]
        assert "Микропроект для исправления" in chat_prompt[1]["content"]

    def test_parser_returns_parse_project_markdown(self):
        """Test that the parser is set to parse_project_markdown."""
        project_markdown = "# Test Project"
        sandbox_result = SandboxResult(stdout="", stderr="", exit_code=0)
        
        generator = BugFixerPromptGenerator(project_markdown, sandbox_result)
        
        # The parser should be the parse_project_markdown function
        from aipg.prompting.utils import parse_project_markdown
        assert generator.parser == parse_project_markdown
