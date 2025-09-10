import difflib
import json
import logging
import re
from typing import Any, Dict, Iterable, Optional

import json_repair
import yaml

from aipg.exceptions import OutputParserException
from aipg.state import Project

logger = logging.getLogger(__name__)


# Pre-compiled regexes for performance
_MD_HEADER_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*(?:#+\s*)?$")
_MD_FENCE_RE = re.compile(r"^\s*([`~]{3,})(.*)$")


def parse_json(raw_reply: str) -> Optional[Dict[str, Any]]:
    def try_json_loads(data: str) -> Dict[str, Any] | None:
        try:
            repaired_json = json_repair.repair_json(
                data, ensure_ascii=False, return_objects=True
            )
            return (
                repaired_json
                if repaired_json and isinstance(repaired_json, dict)
                else None
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {e}")
            return None

    raw_reply = raw_reply.strip()

    # Case 1: Check if the JSON is enclosed in triple backticks (prioritize this)
    # Handle nested code blocks by being more specific about the closing pattern
    code_block_match = re.search(
        r"```(?:json)?\s*(.*?)```$", raw_reply, re.DOTALL | re.MULTILINE
    )
    if not code_block_match:
        # Alternative pattern: look for JSON that ends with } followed by backticks
        code_block_match = re.search(
            r"```(?:json)?\s*(.*?)\}\s*```", raw_reply, re.DOTALL
        )

    if code_block_match:
        reply_str = code_block_match.group(1).strip()
        reply = try_json_loads(reply_str)
        if reply is not None:
            return reply

    # Case 2: Look for JSON object directly in the text
    json_match = re.search(r"\{.*\}", raw_reply, re.DOTALL)
    if json_match:
        reply_str = json_match.group(0).strip()
        reply = try_json_loads(reply_str)
        if reply is not None:
            return reply

    # Case 3: Assume the entire string is a JSON object
    return try_json_loads(raw_reply)


def check_json_values(
    parsed_json: Dict,
    valid_values: Optional[Iterable[str]],
    fallback_value: Optional[str],
):
    if valid_values is not None:
        for key, parsed_value in parsed_json.items():
            # Currently only support single parsed value
            if isinstance(parsed_value, list) and len(parsed_value) == 1:
                parsed_value = parsed_value[0]
            if isinstance(parsed_value, str):
                close_matches = difflib.get_close_matches(parsed_value, valid_values)
            else:
                logger.warning(
                    f"Unrecognized parsed value: {parsed_value} for key {key} parsed by the LLM. "
                    f"It has type: {type(parsed_value)}."
                )
                close_matches = []

            if len(close_matches) == 0:
                if fallback_value:
                    logger.warning(
                        f"Unrecognized value: {parsed_value} for key {key} parsed by the LLM. "
                        f"Will use default value: {fallback_value}."
                    )
                    parsed_json[key] = fallback_value
                else:
                    raise ValueError(
                        f"Unrecognized value: {parsed_value} for key {key} parsed by the LLM."
                    )
            else:
                parsed_json[key] = close_matches[0]
    return parsed_json


def parse_and_check_json(
    raw_reply: str,
    expected_keys: Iterable[str],
    valid_values: Optional[Iterable[str]] = None,
    fallback_value: Optional[str] = None,
):
    if json_obj := parse_json(raw_reply):
        for key in expected_keys:
            if key not in json_obj:
                error = (
                    f"Got invalid return object. Expected key `{key}` "
                    f"to be present, but got {json_obj}"
                )
                logging.error(error)
                raise OutputParserException(error)
        try:
            check_json_values(json_obj, valid_values, fallback_value)
        except ValueError as e:
            raise OutputParserException(str(e))
        return json_obj
    raise OutputParserException("JSON decoding error or JSON not found in output")


def get_outer_columns(all_columns, num_columns_each_end=10):
    if len(all_columns) <= num_columns_each_end * 2:
        return list(all_columns)
    return all_columns[:num_columns_each_end] + all_columns[-num_columns_each_end:]


def parse_markdown_headers(markdown_text: str) -> list[tuple[str, str]]:
    """
    Parse a Markdown string and return an ordered list of (header, content) pairs.

    Characteristics:
    - Ignores headers inside fenced code blocks (``` or ~~~, any length >= 3).
    - Preserves the order of sections as they appear in the document.
    - Trims leading/trailing blank lines from each section's content.
    - Treats any ATX-style header level (H1..H6). Setext headers are not considered here.

    Args:
        markdown_text: Raw Markdown string to parse.

    Returns:
        A list of (header_text, content) tuples, where content is the text
        that appears under the header until the next header or end of document.
    """
    if not markdown_text:
        return []

    lines = markdown_text.splitlines()

    sections: list[tuple[str, str]] = []
    current_header: str | None = None
    current_content_lines: list[str] = []

    in_code_fence = False
    fence_char: str = ""
    fence_len: int = 0

    def flush_current_section() -> None:
        nonlocal current_header, current_content_lines
        if current_header is None:
            current_content_lines = []
            return
        # Trim surrounding blank lines for the section content
        start = 0
        end = len(current_content_lines)
        while start < end and current_content_lines[start].strip() == "":
            start += 1
        while end > start and current_content_lines[end - 1].strip() == "":
            end -= 1
        content = "\n".join(current_content_lines[start:end])
        sections.append((current_header, content))
        current_header = None
        current_content_lines = []

    for line in lines:
        # Detect code fences first; headers inside code blocks must be ignored
        fence_match = _MD_FENCE_RE.match(line)
        if fence_match:
            ticks = fence_match.group(1)
            char = ticks[0]
            count = len(ticks)
            if not in_code_fence:
                in_code_fence = True
                fence_char = char
                fence_len = count
                # Fence lines are part of the content if we are inside a section
                if current_header is not None:
                    current_content_lines.append(line)
                continue
            else:
                # Close only if the closing fence matches the opening kind and length
                if char == fence_char and count >= fence_len:
                    in_code_fence = False
                    fence_char = ""
                    fence_len = 0
                    if current_header is not None:
                        current_content_lines.append(line)
                    continue

        if in_code_fence:
            if current_header is not None:
                current_content_lines.append(line)
            # Ignore header detection while in code
            continue

        header_match = _MD_HEADER_RE.match(line)
        if header_match:
            # New header starts; flush previous section if any
            flush_current_section()
            header_text = header_match.group(2).strip()
            current_header = header_text
            current_content_lines = []
            continue

        # Regular content line (only record if we have already seen a header)
        if current_header is not None:
            current_content_lines.append(line)

    # Flush the last section at EOF
    flush_current_section()

    return sections


def extract_code_block(
    raw_reply: str,
    prefer_languages: Optional[Iterable[str]] = None,
    return_fenced: bool = True,
    strip_trailing_newlines: bool = True,
) -> Optional[str]:
    """
    Extract a fenced code block from a Markdown-like string efficiently.

    Characteristics:
    - Single-pass scan over lines for speed.
    - Supports backtick or tilde fences of any length (>=3).
    - Matches closing fence when same char and length or longer (CommonMark behavior).
    - Preserves original fence characters/length and optional language tag when returning fenced text.
    - If `prefer_languages` is provided, returns only a block whose language
      matches one of the preferences; otherwise returns None.

    Args:
        raw_reply: Input text possibly containing fenced code blocks.
        prefer_languages: Optional iterable of language names to prioritize.
        return_fenced: If True, returns the entire fenced block (including fences);
            otherwise returns only the inner code content.
        strip_trailing_newlines: If True, trims trailing newlines in the inner code content.

    Returns:
        The selected code block as a string, or None if no fenced block is found.
    """
    if not raw_reply:
        return None

    preferred: set[str] | None = (
        set(lang.lower() for lang in prefer_languages) if prefer_languages else None
    )

    lines = raw_reply.splitlines()

    in_fence = False
    fence_char: str = ""
    fence_len: int = 0
    language_hint: str | None = None
    buffer: list[str] = []

    first_block_fenced: str | None = None

    def make_fenced(code_text: str, lang: Optional[str], ticks: str) -> str:
        if strip_trailing_newlines:
            # Normalize trailing newlines for cleaner output while preserving inner content
            code_text = code_text.rstrip("\n")
        lang_suffix = (" " + lang) if lang else ""
        return f"{ticks}{lang_suffix}\n{code_text}\n{ticks}"

    for line in lines:
        fence_match = _MD_FENCE_RE.match(line)
        if fence_match:
            ticks = fence_match.group(1)
            char = ticks[0]
            count = len(ticks)
            rest = fence_match.group(2).strip()

            if not in_fence:
                # Opening fence
                in_fence = True
                fence_char = char
                fence_len = count
                language_hint = rest.split()[0] if rest else None
                buffer = []
                continue
            else:
                # Potential closing fence
                if char == fence_char and count >= fence_len:
                    # Close current block
                    code_text = "\n".join(buffer)
                    ticks_str = fence_char * fence_len

                    if preferred:
                        # Only return if language matches one of the preferences
                        if language_hint and language_hint.lower() in preferred:
                            return (
                                make_fenced(code_text, language_hint, ticks_str)
                                if return_fenced
                                else (
                                    code_text.rstrip("\n")
                                    if strip_trailing_newlines
                                    else code_text
                                )
                            )
                        # No match: continue scanning other blocks
                        in_fence = False
                        fence_char = ""
                        fence_len = 0
                        language_hint = None
                        buffer = []
                        continue
                    else:
                        # No preference: return the first encountered block immediately
                        return (
                            make_fenced(code_text, language_hint, ticks_str)
                            if return_fenced
                            else (
                                code_text.rstrip("\n")
                                if strip_trailing_newlines
                                else code_text
                            )
                        )

        if in_fence:
            buffer.append(line)

    # If preferences were provided but no match found: None. Otherwise, return
    # the first block (which would have been returned early already).
    return None if preferred else first_block_fenced


def extract_expected_output(raw_reply: str) -> str:
    """
    Return the expected output from a prompt response efficiently.

    Behavior:
    - If the response contains a fenced code block (possibly preceded by a
      prelude), return the inner content of the first fenced block, with any
      code fence markers inside that content removed.
    - If there is no fenced block, return the original text with all code fence
      markers removed and then trimmed.

    This function performs at most a single pass over the text by leveraging the
    optimized extractor above.

    Args:
        raw_reply: The full raw response text from the model.

    Returns:
        The extracted code content if a fenced block exists, otherwise the
        trimmed original text.
    """
    if not raw_reply:
        return ""

    def _strip_all_fenced_code_markers(text: str) -> str:
        # Remove all fenced code markers while preserving inner content.
        lines = text.splitlines()
        output: list[str] = []
        in_fence = False
        fence_char: str = ""
        fence_len: int = 0

        for line in lines:
            fence_match = _MD_FENCE_RE.match(line)
            if fence_match:
                ticks = fence_match.group(1)
                char = ticks[0]
                count = len(ticks)
                if not in_fence:
                    # Opening fence: start skipping fence lines
                    in_fence = True
                    fence_char = char
                    fence_len = count
                    continue
                else:
                    # Closing fence: only close if kind matches and length is sufficient
                    if char == fence_char and count >= fence_len:
                        in_fence = False
                        fence_char = ""
                        fence_len = 0
                        continue
                    # Otherwise this is content inside a fence (e.g., shorter ticks), keep it
            if not in_fence:
                output.append(line)
            else:
                # Inside a fence: keep content lines, skip only the fence markers themselves
                output.append(line) if not _MD_FENCE_RE.match(line) else None

        return "\n".join(output).strip()

    # Scan once to find top-level fenced blocks and their bounds
    lines = raw_reply.splitlines()
    blocks: list[tuple[int, int, str | None]] = []  # (start_idx, end_idx, lang)
    in_fence = False
    fence_char: str = ""
    fence_len: int = 0
    lang_hint: str | None = None
    start_idx: int = -1

    for idx, line in enumerate(lines):
        m = _MD_FENCE_RE.match(line)
        if m:
            ticks = m.group(1)
            char = ticks[0]
            count = len(ticks)
            rest = m.group(2).strip()
            if not in_fence:
                in_fence = True
                fence_char = char
                fence_len = count
                lang_hint = rest.split()[0] if rest else None
                start_idx = idx
                continue
            else:
                if char == fence_char and count >= fence_len:
                    # close this block
                    blocks.append((start_idx, idx, lang_hint))
                    in_fence = False
                    fence_char = ""
                    fence_len = 0
                    lang_hint = None
                    start_idx = -1
                    continue
        # otherwise a regular content line; keep scanning

    if len(blocks) == 0:
        # No fenced blocks: just remove any stray fence-like markers and trim
        return _strip_all_fenced_code_markers(raw_reply)

    if len(blocks) == 1:
        b_start, b_end, b_lang = blocks[0]
        has_outside_nonblank = any(
            line.strip() for line in lines[:b_start] + lines[b_end + 1 :]
        )
        # Prefer inner content for outer markdown blocks even if prelude/outro exists
        if (
            b_lang and b_lang.lower() in {"markdown", "md"}
        ) or not has_outside_nonblank:
            inner = "\n".join(lines[b_start + 1 : b_end])
            return _strip_all_fenced_code_markers(inner)
        # Otherwise the fenced block is embedded inside other meaningful text:
        # remove all fence markers across the entire text and return.
        return _strip_all_fenced_code_markers(raw_reply)

    # Multiple fenced blocks detected: treat as mixed content document, remove all markers.
    return _strip_all_fenced_code_markers(raw_reply)


def _normalize_header_name(header_text: str) -> str:
    # Lowercase and collapse internal whitespace for robust matching
    return re.sub(r"\s+", " ", header_text.strip().lower())


def _parse_topic_from_h1(header_text: str) -> Optional[str]:
    # Expect pattern like: "Микропроект для углубления темы: <topic>"
    if ":" not in header_text:
        return None
    _, after = header_text.split(":", 1)
    topic = after.strip()
    # Strip surrounding brackets if present
    if topic.startswith("[") and topic.endswith("]"):
        topic = topic[1:-1].strip()
    return topic or None


def parse_project_markdown(raw_markdown: str) -> Project:
    """
    Parse a project markdown document into a Project model.

    Fast path notes:
    - Pre-strips an outer ```markdown fenced block to allow header scanning.
    - Single pass header parsing using parse_markdown_headers (ignores code fences correctly).
    - Uses optimized code/expected extractors.
    """
    if not raw_markdown or not raw_markdown.strip():
        raise OutputParserException(
            "Empty markdown provided",
            expected=[
                "# Микропроект для углубления темы: <Тема>",
                "## Цель микропроекта",
                "## Описание микропроекта",
                "## Входные данные",
                "## Ожидаемый результат",
                "## Эталонное решение",
                "## Автотест",
            ],
            got="<empty>",
        )

    # If the whole response is wrapped in a top-level ```markdown fenced block,
    # unwrap only that outer block while preserving inner fences for later parsing.
    def _unwrap_outer_markdown_block(text: str) -> str:
        if not text:
            return text
        lines = text.splitlines()
        # Find first non-blank line
        start = 0
        while start < len(lines) and lines[start].strip() == "":
            start += 1
        if start >= len(lines):
            return text
        m_open = _MD_FENCE_RE.match(lines[start])
        if not m_open:
            return text
        ticks = m_open.group(1)
        char = ticks[0]
        count = len(ticks)
        rest = m_open.group(2).strip()
        lang = rest.split()[0].lower() if rest else None
        # Allow unwrapping when explicitly markdown/md or when no language is provided
        if lang not in {"markdown", "md"} and lang is not None:
            return text
        # Find last non-blank line
        end = len(lines) - 1
        while end >= 0 and lines[end].strip() == "":
            end -= 1
        if end <= start:
            return text
        m_close = _MD_FENCE_RE.match(lines[end])
        if not (
            m_close and m_close.group(1)[0] == char and len(m_close.group(1)) >= count
        ):
            return text
        # Unwrap inner content without stripping any internal fences
        inner = "\n".join(lines[start + 1 : end])
        return inner

    def _strip_conversational_text(text: str) -> str:
        """Remove any conversational text before the actual markdown content."""
        if not text:
            return text

        lines = text.splitlines()
        # Look for the first line that starts with "# Микропроект для углубления темы:"
        for i, line in enumerate(lines):
            if line.strip().startswith("# Микропроект для углубления темы:"):
                # Return everything from this line onwards
                return "\n".join(lines[i:])

        # If no such header found, return original text
        return text

    preprocessed = _unwrap_outer_markdown_block(raw_markdown)
    preprocessed = _strip_conversational_text(preprocessed)

    sections = parse_markdown_headers(preprocessed)
    if not sections:
        raise OutputParserException(
            "No top-level headers found",
            expected=["H1 and H2 headers per template"],
            got=preprocessed[:500],
        )

    # Map sections by normalized header
    normalized_map: dict[str, str] = {}
    first_h1: Optional[str] = None
    for header, content in sections:
        norm = _normalize_header_name(header)
        if first_h1 is None:
            first_h1 = header
        normalized_map[norm] = content

    # Extract topic from first H1
    topic = _parse_topic_from_h1(first_h1 or "")
    if not topic:
        raise OutputParserException(
            "Failed to parse topic from H1",
            expected="'# Микропроект для углубления темы: <Тема>'",
            got=first_h1 or "<missing>",
        )

    # Expected section keys in Russian as in the template
    key_map = {
        "цель микропроекта": "goal",
        "описание микропроекта": "description",
        "входные данные": "input_data",
        "ожидаемый результат": "expected_output_raw",
        "эталонное решение": "expert_solution_raw",
        "автотест": "autotest_raw",
    }

    collected: dict[str, str] = {}
    missing: list[str] = []
    for human_key, internal_name in key_map.items():
        norm_key = human_key
        found_content = None
        # exact match first
        if norm_key in normalized_map:
            found_content = normalized_map[norm_key]
        else:
            # try startswith to be resilient to minor suffixes (none expected, but safe)
            for k, v in normalized_map.items():
                if k.startswith(norm_key):
                    found_content = v
                    break
        if found_content is None:
            missing.append(human_key)
        else:
            collected[internal_name] = found_content

    if missing:
        raise OutputParserException(
            "Missing required sections",
            expected=missing,
            got=", ".join(normalized_map.keys()),
            details={"present_headers": list(normalized_map.keys())},
        )

    # Extract refined fields
    expected_output = extract_expected_output(collected["expected_output_raw"]) or ""

    def _find_first_fenced_block(text: str) -> tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        lines = text.splitlines()
        in_fence = False
        fence_char = ""
        fence_len = 0
        lang_hint: Optional[str] = None
        buf: list[str] = []
        for line in lines:
            m = _MD_FENCE_RE.match(line)
            if m:
                ticks = m.group(1)
                char = ticks[0]
                count = len(ticks)
                rest = m.group(2).strip()
                if not in_fence:
                    in_fence = True
                    fence_char = char
                    fence_len = count
                    lang_hint = rest.split()[0] if rest else None
                    buf = []
                    continue
                else:
                    if char == fence_char and count >= fence_len:
                        code_text = "\n".join(buf).rstrip("\n")
                        return lang_hint, code_text
                    # shorter/other fence inside content; treat as content
            if in_fence:
                buf.append(line)
        return None, None

    # Expert solution: require a fenced code block (any language)
    exp_lang, exp_code = _find_first_fenced_block(collected["expert_solution_raw"])
    if exp_code is None:
        raise OutputParserException(
            "Code block not found in 'Эталонное решение' section",
            expected="A fenced code block with the expert solution",
            got=collected["expert_solution_raw"][:500],
            details={"section": "Эталонное решение", "lang_detected": exp_lang},
        )
    expert_solution_block = exp_code

    # Autotest: must be Python fenced code block
    auto_lang, auto_code = _find_first_fenced_block(collected["autotest_raw"])
    if auto_code is None:
        raise OutputParserException(
            "Code block not found in 'Автотест' section",
            expected="A fenced Python code block with the autotest",
            got=collected["autotest_raw"][:500],
            details={"section": "Автотест", "lang_detected": auto_lang},
        )
    allowed_python_langs = {"python", "py"}
    if not (auto_lang and auto_lang.lower() in allowed_python_langs):
        raise OutputParserException(
            "Автотест должен быть предоставлен на Python (fenced code block)",
            expected="```python\n...\n```",
            got=f"lang={auto_lang or '<none>'}",
            details={"section": "Автотест"},
        )
    autotest_block = auto_code

    return Project(
        raw_markdown=preprocessed,
        topic=topic,
        goal=collected["goal"].strip(),
        description=collected["description"].strip(),
        input_data=collected["input_data"].strip(),
        expected_output=expected_output,
        expert_solution=expert_solution_block,
        autotest=autotest_block,
    )


def parse_llm_ranker_scores(raw_reply: str) -> list[float]:
    """
    Parse LLM ranker response and return a list of similarity scores.

    Accepts responses that are either:
    - A JSON fenced code block (```json ... ```), or
    - Raw JSON text, or
    - A plain JSON array (fallback)

    Returns a list of float scores in [0,1] range.
    Raises OutputParserException for invalid JSON or unsupported structures.
    """
    if not raw_reply or not raw_reply.strip():
        return []

    # Prefer extracting a JSON fenced code block; fall back to first fenced block; then raw text
    code_text = (
        extract_code_block(raw_reply, prefer_languages=("json",), return_fenced=False)
        or extract_code_block(raw_reply, return_fenced=False)
        or raw_reply
    )

    # Try to extract JSON array from text if it's not pure JSON
    if not code_text.strip().startswith("["):
        # Look for a JSON array at the start of the text or after some text
        json_match = re.search(r"\[[^\]]*\]", code_text)
        if json_match:
            code_text = json_match.group(0)

    try:
        loaded = json.loads(code_text)
    except json.JSONDecodeError as e:
        raise OutputParserException(
            "Failed to parse JSON",
            expected="JSON array of floats, e.g. [0.8, 0.2, 0.9]",
            got=code_text[:500],
            details={"error": str(e)},
        )

    # Validate that we got a list
    if not isinstance(loaded, list):
        raise OutputParserException(
            "Expected JSON array",
            expected="JSON array of floats, e.g. [0.8, 0.2, 0.9]",
            got=str(type(loaded)),
        )

    # Convert to floats and validate range
    scores: list[float] = []
    for i, item in enumerate(loaded):
        try:
            score = float(item)
            if not (0.0 <= score <= 1.0):
                raise OutputParserException(
                    f"Score out of range at index {i}",
                    expected="Float between 0.0 and 1.0",
                    got=str(score),
                )
            scores.append(score)
        except (ValueError, TypeError) as e:
            raise OutputParserException(
                f"Invalid score at index {i}",
                expected="Float between 0.0 and 1.0",
                got=str(item),
                details={"error": str(e)},
            )

    return scores


def parse_define_topics(raw_reply: str) -> list[str]:
    """
    Parse YAML from the model response and return a normalized list of topics.

    Accepts responses that are either:
    - A YAML fenced code block (```yaml ... ```), or
    - Raw YAML text, or
    - A plain YAML list (fallback: treated as topics directly)

    Returns a de-duplicated list of non-empty string topics.
    Raises OutputParserException for invalid YAML or unsupported structures.
    """
    if not raw_reply or not raw_reply.strip():
        return []

    # Prefer extracting a YAML/YML fenced code block; fall back to first fenced block; then raw text
    code_text = (
        extract_code_block(
            raw_reply, prefer_languages=("yaml", "yml"), return_fenced=False
        )
        or extract_code_block(raw_reply, return_fenced=False)
        or raw_reply
    )

    try:
        loaded = yaml.safe_load(code_text)
    except yaml.YAMLError as e:
        raise OutputParserException(
            "Failed to parse YAML",
            expected="YAML with a 'topics' list, e.g. topics: []",
            got=code_text[:500],
            details={"error": str(e)},
        )

    # Determine topics list from loaded YAML structure
    topics_value: list[str] | None
    if isinstance(loaded, dict):
        topics_value = loaded.get("topics", [])
    elif isinstance(loaded, list):
        topics_value = loaded
    elif loaded is None:
        topics_value = []
    else:
        raise OutputParserException(
            "Unsupported YAML root type",
            expected="mapping with 'topics' key or a list of strings",
            got=str(type(loaded)),
        )

    if not isinstance(topics_value, list):
        raise OutputParserException(
            "'topics' must be a list",
            expected='topics: ["Topic 1", "Topic 2"]',
            got=str(type(topics_value)),
        )

    # Normalize: keep only non-empty strings, strip whitespace, de-duplicate preserving order
    normalized: list[str] = []
    seen: set[str] = set()
    for item in topics_value:
        if isinstance(item, str):
            topic = item.strip()
            if topic and topic not in seen:
                seen.add(topic)
                normalized.append(topic)
        else:
            logger.warning(
                "Ignoring non-string topic entry: %r (type=%s)", item, type(item)
            )

    return normalized
