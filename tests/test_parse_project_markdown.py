import pytest
from aipg.exceptions import OutputParserException
from aipg.prompting.utils import parse_project_markdown


def _build_markdown(
    wrap_all: bool,
    autotest_lang: str,
    topic_bracketed: bool,
    expected_fenced: bool,
):
    topic_text = "Сортировка массивов"
    h1_topic = f"[{topic_text}]" if topic_bracketed else topic_text

    goal_text = "Найти эффективный метод сортировки."
    desc_text = "Реализуйте алгоритм сортировки для целых чисел."
    input_text = "Список целых чисел."

    if expected_fenced:
        expected_section = """
```text
Отсортированный список чисел в порядке возрастания.
```
""".strip()
    else:
        expected_section = "Отсортированный список чисел в порядке возрастания."

    expert_code_inner = "print('solution')\n"
    expert_section = f"""
```python
{expert_code_inner}
```
""".strip()

    autotest_code_inner = "def test_sorting():\n    assert sorted([3,1,2]) == [1,2,3]\n"
    autotest_section = f"""
```{autotest_lang}
{autotest_code_inner}
```
""".strip()

    doc = f"""
# Микропроект для углубления темы: {h1_topic}

## Цель микропроекта
{goal_text}

## Описание микропроекта
{desc_text}

## Входные данные
{input_text}

## Ожидаемый результат
{expected_section}

## Эталонное решение
{expert_section}

## Автотест
{autotest_section}
""".strip()

    if wrap_all:
        return f"""
```markdown
{doc}
```
""".strip()
    return doc


@pytest.mark.parametrize(
    "wrap_all,autotest_lang,topic_bracketed,expected_fenced",
    [
        (False, "python", False, True),
        (True, "py", True, False),
        (True, "python", True, True),
        (False, "py", False, False),
    ],
)
def test_parse_project_markdown_success_variations(
    wrap_all: bool, autotest_lang: str, topic_bracketed: bool, expected_fenced: bool
):
    raw = _build_markdown(
        wrap_all=wrap_all,
        autotest_lang=autotest_lang,
        topic_bracketed=topic_bracketed,
        expected_fenced=expected_fenced,
    )

    result = parse_project_markdown(raw)

    expected_topic = "Сортировка массивов"
    assert result.topic == expected_topic

    # Core fields should be preserved (trimmed) as given
    assert "Найти эффективный метод сортировки." == result.goal
    assert "Реализуйте алгоритм сортировки для целых чисел." == result.description
    assert "Список целых чисел." == result.input_data

    # Expected output should have no fenced markers and include our content
    assert "```" not in result.expected_output
    assert "Отсортированный список чисел" in result.expected_output

    # Expert solution and autotest should return inner code only (no fences)
    assert "```" not in result.expert_solution
    assert "print('solution')" in result.expert_solution

    assert "```" not in result.autotest
    assert "def test_sorting():" in result.autotest
    assert "assert sorted([3,1,2]) == [1,2,3]" in result.autotest


# --- Error cases ---


def _valid_doc(
    *,
    h1: str = "# Микропроект для углубления темы: Сортировка массивов",
    include_autotest: bool = True,
    expert_fenced: bool = True,
    autotest_fenced: bool = True,
    autotest_lang: str = "python",
):
    goal = "Найти эффективный метод сортировки."
    desc = "Реализуйте алгоритм сортировки для целых чисел."
    input_data = "Список целых чисел."
    expected = "Отсортированный список чисел в порядке возрастания."

    expected_section = f"""
```text
{expected}
```
""".strip()

    expert_section = (
        """
```python
print('solution')
```
""".strip()
        if expert_fenced
        else "print('solution')"
    )

    autotest_body = (
        f"""
```{autotest_lang}
def test_sorting():
    assert sorted([3,1,2]) == [1,2,3]
```
""".strip()
        if autotest_fenced
        else "def test_sorting():\n    assert sorted([3,1,2]) == [1,2,3]"
    )

    parts = [
        h1,
        "\n## Цель микропроекта\n" + goal,
        "\n## Описание микропроекта\n" + desc,
        "\n## Входные данные\n" + input_data,
        "\n## Ожидаемый результат\n" + expected_section,
        "\n## Эталонное решение\n" + expert_section,
    ]
    if include_autotest:
        parts.append("\n## Автотест\n" + autotest_body)
    return "\n".join(parts).strip()


@pytest.mark.parametrize(
    "raw, check",
    [
        ("", lambda e: (e.got == "<empty>" and isinstance(e.expected, list))),
        (
            "Просто текст без заголовков",
            lambda e: (
                isinstance(e.expected, list)
                and len(e.expected) == 1
                and isinstance(e.expected[0], str)
                and "H1" in e.expected[0]
            ),
        ),
        (
            _valid_doc(h1="# Микропроект для углубления темы", autotest_lang="python"),
            lambda e: (
                isinstance(e.expected, str)
                and "Микропроект" in e.expected
                and isinstance(e.got, str)
            ),
        ),
        (
            _valid_doc(include_autotest=False),
            lambda e: (
                isinstance(e.expected, list)
                and any("автотест" in x.lower() for x in e.expected)
                and "present_headers" in e.details
            ),
        ),
        (
            _valid_doc(expert_fenced=False),
            lambda e: (
                e.details.get("section") == "Эталонное решение"
                and isinstance(e.got, str)
            ),
        ),
        (
            _valid_doc(autotest_fenced=False),
            lambda e: (e.details.get("section") == "Автотест"),
        ),
        (
            _valid_doc(autotest_lang="javascript"),
            lambda e: (
                e.details.get("section") == "Автотест"
                and isinstance(e.got, str)
                and e.got.startswith("lang=")
            ),
        ),
    ],
)
def test_parse_project_markdown_raises_cases(raw, check):
    with pytest.raises(OutputParserException) as excinfo:
        parse_project_markdown(raw)
    err = excinfo.value
    assert check(err)


@pytest.mark.parametrize(
    "open_fence",
    [
        "```",
        "```markdown",
        "````markdown",
    ],
)
def test_parse_project_markdown_outer_markdown_fence_success(open_fence: str):
    # Build a valid, unwrapped doc then wrap in the specified outer markdown fence
    inner = _build_markdown(
        wrap_all=False,
        autotest_lang="python",
        topic_bracketed=False,
        expected_fenced=True,
    )
    close_fence = "`" * (open_fence.count("`"))
    raw = f"{open_fence}\n{inner}\n{close_fence}"

    result = parse_project_markdown(raw)
    assert result.topic == "Сортировка массивов"
    assert "Найти эффективный метод сортировки." == result.goal
    assert "```" not in result.expert_solution
    assert "def test_sorting():" in result.autotest
