class OutputParserException(ValueError):
    """Exception that output parsers should raise to signify a parsing error.

    Supports structured details about what was expected and what was actually
    received to help the LLM agent self-correct.
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        expected: str | list[str] | None = None,
        got: str | None = None,
        details: dict | None = None,
    ) -> None:
        # Keep backward compatibility: allow raising with only a message
        parts: list[str] = []
        if message:
            parts.append(message)
        if expected is not None:
            exp_text = (
                ", ".join(expected) if isinstance(expected, list) else str(expected)
            )
            parts.append(f"expected: {exp_text}")
        if got is not None:
            # Truncate overly long values to keep logs readable
            got_text = got if len(got) <= 500 else got[:497] + "..."
            parts.append(f"got: {got_text}")
        if details:
            parts.append(f"details: {details}")

        super().__init__("; ".join(parts) if parts else None)
        self.expected = expected
        self.got = got
        self.details = details or {}
    
class OutputValidationException(ValueError):
    """Exception that output validators should raise to signify a validation error."""
