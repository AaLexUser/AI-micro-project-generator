# 🤝 Contributing to AI Micro-Project Generator

<div align="center">

*Thank you for your interest in contributing to the AI Micro-Project Generator!*

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/AaLexUser/AI-micro-project-generator/pulls)
[![Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-contributor%20covenant-green.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🌟 Welcome Contributors!

We're excited to have you contribute to this project! Whether you're fixing bugs, adding features, improving documentation, or helping with testing, every contribution is valuable and appreciated.

This guide will help you get started and ensure your contributions align with our project standards and philosophy.

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🎯 Ways to Contribute](#-ways-to-contribute)
- [🛠️ Development Setup](#%EF%B8%8F-development-setup)
- [🏗️ Development Workflow](#%EF%B8%8F-development-workflow)
- [✅ Code Quality Standards](#-code-quality-standards)
- [🧪 Testing Guidelines](#-testing-guidelines)
- [📝 Documentation Standards](#-documentation-standards)
- [🎨 Frontend Contribution Guidelines](#-frontend-contribution-guidelines)
- [🔧 Code Style & Formatting](#-code-style--formatting)
- [📦 Commit Message Guidelines](#-commit-message-guidelines)
- [🚀 Pull Request Process](#-pull-request-process)
- [🐛 Bug Reports](#-bug-reports)
- [💡 Feature Requests](#-feature-requests)
- [❓ Getting Help](#-getting-help)

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

- **Python 3.12+** ([Download](https://python.org))
- **[uv](https://github.com/astral-sh/uv)** - Modern Python package manager
- **Docker** ([Download](https://docker.com)) - For sandbox testing and deployment
- **Node.js 18+** ([Download](https://nodejs.org)) - For frontend development
- **Git** ([Download](https://git-scm.com))

### 🔄 Fork & Clone

1. **Fork the repository** on GitHub
2. **Clone your fork locally:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AI-micro-project-generator.git
   cd AI-micro-project-generator
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/AaLexUser/AI-micro-project-generator.git
   ```

---

## 🎯 Ways to Contribute

### 🐛 Bug Fixes
- Fix existing issues
- Improve error handling
- Performance optimizations
- Security improvements

### ✨ New Features
- AI assistant improvements
- New inference algorithms
- Enhanced sandbox capabilities
- API enhancements
- Frontend features

### 📚 Documentation
- Code documentation
- User guides
- API documentation
- Tutorial improvements

### 🧪 Testing
- Unit tests
- Integration tests
- End-to-end tests
- Performance tests

### 🎨 Design & UX
- UI/UX improvements
- Accessibility enhancements
- Mobile responsiveness
- Visual design

### 🔧 DevOps & Infrastructure
- Docker improvements
- CI/CD enhancements
- Deployment optimizations
- Monitoring and logging

---

## 🛠️ Development Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
uv sync --group dev

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configuration Setup

```bash
# Copy example configuration
cd aipg/configs
cp default.yaml.example default.yaml

# Edit configuration with your API keys
nano default.yaml
```

**Required configuration:**
```yaml
llm:
  model_name: "openai/gpt-4o"  # or "gemini/gemini-2.0-flash"
  api_key: "your-api-key-here"
```

### 3. Pre-commit Hooks

```bash
# Install pre-commit hooks for code quality
make pre-commit-install
```

### 4. Build Docker Images

```bash
# Build all required Docker images
make docker-build
```

### 5. Verify Setup

```bash
# Run quality checks
make quality

# Run tests
uv run pytest tests/ -v

# Start development server
uv run python -m aipg.api

# In another terminal, start frontend
cd frontend && npm run dev
```

---

## 🏗️ Development Workflow

### 1. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create and switch to feature branch
git checkout -b feature/amazing-feature
```

### 2. Make Changes

- Follow our [code style guidelines](#-code-style--formatting)
- Add tests for new functionality
- Update documentation as needed
- Ensure all quality checks pass

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest tests/ -v

# Run quality checks
make quality

# Test specific components if applicable
uv run pytest tests/sandbox/ -v  # For sandbox changes
uv run pytest tests/task_inference/ -v  # For AI inference changes
```

### 4. Commit and Push

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add amazing new feature

- Implement core functionality
- Add comprehensive tests
- Update documentation"

# Push to your fork
git push origin feature/amazing-feature
```

### 5. Create Pull Request

- Navigate to your fork on GitHub
- Click "New Pull Request"
- Fill out the PR template
- Request review from maintainers

---

## ✅ Code Quality Standards

### 🎯 Core Principles

1. **Clarity over Cleverness** - Write code that's easy to understand
2. **Modularity** - Keep components focused and loosely coupled
3. **Testability** - Design for easy testing and mocking
4. **Documentation** - Document complex logic and public APIs
5. **Performance** - Consider performance implications, especially for AI operations

### 🔍 Quality Checks

We maintain high code quality through automated checks:

```bash
# Run all quality checks
make quality

# Individual checks
make lint          # Code linting with ruff
make lint-fix      # Auto-fix linting issues
make format        # Code formatting and import organization
```

### 📊 Code Metrics

- **Line Length**: Maximum 100 characters
- **Function Length**: Keep functions focused and under 50 lines when possible
- **Complexity**: Avoid deeply nested logic; prefer early returns
- **Type Hints**: Use type hints for all public functions and complex logic

---

## 🧪 Testing Guidelines

We follow strict testing principles to ensure code quality and maintainability:

### 📜 Core Philosophy: The Black-Box Principle

> Treat each function as an opaque black box. Tests must **only** validate externally visible behavior (input/output relationships). This allows complete internal refactoring **without breaking tests**.

### ✅ Strict Requirements

#### 1. **Mock Only External Dependencies**
- **✅ Mock**: API calls, database connections, LLM calls, file system operations
- **❌ Don't Mock**: Internal function calls within your module
- **Example**: Mock `litellm.completion()` but not internal helper functions

```python
# ✅ Good - Mock external dependency
@patch('aipg.llm.litellm.completion')
def test_generate_project(mock_llm):
    mock_llm.return_value = MockResponse("Generated project")
    result = generate_project("user input")
    assert "Generated project" in result.content

# ❌ Bad - Mocking internal implementation
@patch('aipg.assistant._validate_project')  # Internal function
def test_generate_project(mock_validate):
    # This breaks when we refactor internal logic
```

#### 2. **Focus on Main Use Cases**
- Write the **minimum number of tests** for primary success paths
- Prioritize easy maintenance over high code coverage
- Use parametrization for testing input variations

```python
# ✅ Good - Single parameterized test
@pytest.mark.parametrize("user_input,expected_topic", [
    ("I struggle with Python loops", "loops"),
    ("Can't understand async/await", "async"),
    ("Database queries are confusing", "database"),
])
def test_extract_topics_success(user_input, expected_topic):
    result = extract_topics(user_input)
    assert expected_topic in [topic.name for topic in result]

# ❌ Bad - Multiple similar tests
def test_extract_loops_topic():
    result = extract_topics("I struggle with Python loops")
    assert "loops" in [topic.name for topic in result]

def test_extract_async_topic():
    result = extract_topics("Can't understand async/await")
    assert "async" in [topic.name for topic in result]
```

#### 3. **Test Predictable Failures**
- Add **minimal tests** for 1-2 predictable failure modes
- Assert on **exception type**, not error message strings

```python
# ✅ Good - Test exception type
def test_generate_project_invalid_input():
    with pytest.raises(ValueError):
        generate_project("")

# ❌ Bad - Testing error message (brittle)
def test_generate_project_invalid_input():
    with pytest.raises(ValueError, match="Input cannot be empty"):
        generate_project("")
```

### ❌ Critical Rules: Avoid Implementation Details

**DO NOT test:**
- Private methods (methods starting with `_`)
- Internal state or data structures
- Sequence of internal operations
- Exact string formatting (unless it's the core feature)

```python
# ❌ Bad - Testing internal implementation
def test_project_generation_calls_validator():
    with patch('aipg.assistant._validate_project') as mock_validate:
        generate_project("test input")
        mock_validate.assert_called_once()  # Implementation detail!

# ✅ Good - Testing external behavior
def test_project_generation_returns_valid_project():
    result = generate_project("test input")
    assert result.title is not None
    assert result.task_description is not None
    assert len(result.success_criteria) > 0
```

### 🏃‍♂️ Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/ -m unit
uv run pytest tests/ -m integration

# Run tests for specific component
uv run pytest tests/sandbox/ -v
uv run pytest tests/task_inference/ -v

# Run with coverage (optional)
uv run pytest tests/ --cov=aipg
```

### 📁 Test Organization

```
tests/
├── unit/                    # Fast, isolated unit tests
├── integration/            # Component integration tests
├── prompting/              # AI prompt testing
├── rag/                   # RAG system tests
├── sandbox/               # Sandbox execution tests
└── utils/                 # Utility function tests
```

---

## 📝 Documentation Standards

### 📖 Code Documentation

#### Function Documentation
```python
def generate_project(user_comments: list[str], config: AppConfig) -> list[Project]:
    """Generate micro-projects from user issue descriptions.

    Takes user comments describing coding issues or learning challenges
    and generates structured learning projects with tasks, solutions,
    and success criteria.

    Args:
        user_comments: List of user-provided issue descriptions
        config: Application configuration including LLM settings

    Returns:
        List of generated Project objects with complete learning materials

    Raises:
        ValueError: If user_comments is empty or contains invalid input
        LLMError: If AI service is unavailable or returns invalid response
    """
```

#### Class Documentation
```python
class ProjectAssistant:
    """AI assistant for generating structured learning micro-projects.

    Orchestrates the complete project generation pipeline including:
    - Topic extraction from user input
    - RAG-based project discovery
    - New project generation when needed
    - Project validation and correction
    - Automated testing and bug fixing

    Attributes:
        config: Application configuration
        llm_client: Language model client for AI operations
        rag_service: Retrieval-augmented generation service
        sandbox_service: Safe code execution environment
    """
```

### 📚 README Updates

When adding new features, update relevant sections in `README.md`:
- Features list
- Usage examples
- Configuration options
- API documentation

---

## 🎨 Frontend Contribution Guidelines

### 🛠️ Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **React Router** for navigation
- **React Hook Form** for form handling
- **Vite** for development and building

### 🎯 Frontend Standards

#### Component Structure
```typescript
// ✅ Good component structure
interface ProjectCardProps {
  project: Project;
  onSelect: (projectId: string) => void;
  className?: string;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onSelect,
  className = "",
}) => {
  const handleClick = useCallback(() => {
    onSelect(project.id);
  }, [project.id, onSelect]);

  return (
    <Card className={cn("cursor-pointer hover:shadow-lg", className)}>
      {/* Component content */}
    </Card>
  );
};
```

#### Styling Guidelines
- Use Tailwind CSS classes for styling
- Follow existing design patterns
- Ensure responsive design (mobile-first)
- Use semantic HTML elements
- Follow accessibility best practices

#### State Management
- Use React hooks for local state
- Keep state close to where it's used
- Use React Query for server state (if applicable)
- Prefer derived state over storing computed values

### 🚀 Frontend Development

```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

---

## 🔧 Code Style & Formatting

### 🐍 Python Style

We use **Ruff** for linting and formatting:

```bash
# Check code style
make lint

# Auto-fix issues
make lint-fix

# Format code
make format
```

#### Key Style Guidelines

- **Line length**: 100 characters maximum
- **Imports**: Organized automatically by ruff
- **Type hints**: Required for public functions
- **Docstrings**: Use Google-style docstrings
- **Variable names**: Use descriptive names, avoid abbreviations

#### Example Code Style
```python
from typing import Optional

from aipg.domain import Project
from aipg.exceptions import ValidationError


class ProjectValidator:
    """Validates generated projects for completeness and correctness."""

    def __init__(self, strict_mode: bool = False) -> None:
        self.strict_mode = strict_mode

    def validate_project(self, project: Project) -> Optional[ValidationError]:
        """Validate a project for required fields and logical consistency.

        Args:
            project: The project to validate

        Returns:
            ValidationError if validation fails, None if valid
        """
        if not project.title or len(project.title.strip()) < 5:
            return ValidationError("Project title must be at least 5 characters")

        if not project.task_description:
            return ValidationError("Project must have a task description")

        return None
```

### 🎨 TypeScript/React Style

- **Prefer functional components** with hooks
- **Use TypeScript interfaces** for props and data structures
- **Follow React best practices** (hooks rules, key props, etc.)
- **Use semantic HTML** elements
- **Implement proper error boundaries**

---

## 📦 Commit Message Guidelines

We follow the [Conventional Commits](https://conventionalcommits.org/) specification:

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature addition
git commit -m "feat(rag): add similarity threshold configuration

- Add configurable similarity threshold for RAG retrieval
- Update default configuration with new parameter
- Add tests for threshold validation"

# Bug fix
git commit -m "fix(sandbox): resolve memory leak in Docker containers

- Properly cleanup container resources after execution
- Add timeout handling for long-running processes
- Update container resource limits"

# Documentation update
git commit -m "docs: add detailed API usage examples

- Add curl examples for all endpoints
- Include response format documentation
- Update error handling section"
```

---

## 🚀 Pull Request Process

### 📝 PR Template

When creating a pull request, please include:

#### Description
- **What does this PR do?** Brief overview of changes
- **Why is this change needed?** Context and motivation
- **How has this been tested?** Testing approach and results

#### Changes
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring
- [ ] Test improvement

#### Checklist
- [ ] I have read the contributing guidelines
- [ ] My code follows the project style guidelines
- [ ] I have added tests for new functionality
- [ ] All existing tests pass
- [ ] I have updated documentation as needed
- [ ] My commit messages follow the conventional commits format

### 🔍 Review Process

1. **Automated Checks**: CI runs tests and quality checks
2. **Code Review**: Maintainers review code for:
   - Functionality correctness
   - Code quality and style
   - Test coverage
   - Documentation completeness
3. **Feedback**: Address review comments and update PR
4. **Approval**: PR is approved and merged by maintainer

### ⚡ Merge Requirements

- [ ] All CI checks pass
- [ ] At least one maintainer approval
- [ ] No merge conflicts
- [ ] Documentation updated if needed
- [ ] Tests added for new functionality

---

## 🐛 Bug Reports

### 🔍 Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Try the latest version** to see if it's already fixed
3. **Check documentation** for known limitations

### 📝 Bug Report Template

**Title**: Brief, descriptive title

**Description**:
- What happened?
- What did you expect to happen?
- Steps to reproduce the issue

**Environment**:
- OS: (e.g., macOS 13.0)
- Python version: (e.g., 3.12.1)
- Package version: (e.g., 0.1.0)
- Docker version: (if applicable)

**Logs/Screenshots**:
- Include relevant error messages
- Add screenshots if applicable
- Attach log files if helpful

**Minimal Reproduction**:
```python
# Minimal code example that reproduces the issue
from aipg import generate_project

# This causes the error
result = generate_project([])
```

---

## 💡 Feature Requests

### 🎯 Feature Request Template

**Title**: Clear, concise feature description

**Problem Statement**:
- What problem does this solve?
- Who would benefit from this feature?
- What's the current workaround?

**Proposed Solution**:
- Detailed description of the feature
- How should it work?
- Example usage

**Alternatives Considered**:
- What other approaches did you consider?
- Why is this the best solution?

**Additional Context**:
- Mockups, diagrams, or examples
- Related issues or discussions
- Implementation considerations

---

## ❓ Getting Help

### 💬 Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Code Review**: PR discussions and feedback

### 🤝 Community Guidelines

- **Be respectful** and inclusive
- **Help others** when you can
- **Stay on topic** in discussions
- **Provide context** when asking questions
- **Search before asking** to avoid duplicates

### 📚 Resources

- **[Project README](README.md)**: Complete project documentation
- **[API Documentation](docs/api.md)**: Detailed API reference
- **[Development Guide](docs/development.md)**: In-depth development setup

---

## 🙏 Recognition

### 🏆 Contributors

All contributors are recognized in our:
- GitHub contributors list
- Release notes for significant contributions
- Special recognition for long-term contributors

### 🎖️ Types of Recognition

- **Code Contributors**: Bug fixes, features, refactoring
- **Documentation Contributors**: Docs, guides, examples
- **Community Contributors**: Helping others, issue triage
- **Design Contributors**: UI/UX improvements, accessibility

---

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

<div align="center">

## 🎉 Thank You!

**Your contributions make this project better for everyone!**

Whether you're fixing a typo, adding a feature, or helping other contributors, every contribution matters and is appreciated.

**[⬆ Back to Top](#-contributing-to-ai-micro-project-generator)**

---

*Made with ❤️ by the AIPG Community*

</div>
