# Tests

This directory contains comprehensive tests for the AIPG project.

## Running Tests

### Using uv (recommended)

Run all tests:
```bash
uv run pytest tests/
```

Run tests with verbose output:
```bash
uv run pytest tests/ -v
```

Run only unit tests:
```bash
uv run pytest tests/ -m unit
```

Run a specific test file:
```bash
uv run pytest tests/test_parse_markdown_headers.py -v
```

Run a specific test:
```bash
uv run pytest tests/test_parse_markdown_headers.py::test_multiple_headers_order_and_content -v
```

### Test's Guidelines

1. Mock all external calls (e.g LLM calls).
2. Do not test internal implementation, test only externally visible behaviour.
3. Prefer easy maintenance over high coverage.
4. Do not test implementation details; only test visible behaviour that defines the API specification.
The presence of specific text in the output is an implementation detail.
5. Prefer freedom for future refactoring and flexibility to change implementation without breaking tests.
6. Use parametrization to combine different inputs into a single test.
7. The number of tests should be sufficient to cover the main use case and no more. Prefer as few tests and as little code as possible.
