import pytest

from aipg.prompting.utils import parse_markdown_headers


@pytest.mark.unit
def test_empty_string_returns_empty_list():
    assert parse_markdown_headers("") == []


@pytest.mark.unit
def test_single_header_with_trimmed_content():
    md = """# Title

line 1

line 2
"""
    sections = parse_markdown_headers(md)
    assert sections == [("Title", "line 1\n\nline 2")]


@pytest.mark.unit
def test_multiple_headers_order_and_content():
    md = """# First
alpha
## Second
beta
# Third

"""
    sections = parse_markdown_headers(md)
    assert sections == [
        ("First", "alpha"),
        ("Second", "beta"),
        ("Third", ""),
    ]


@pytest.mark.unit
def test_headers_inside_backtick_code_fence_are_ignored():
    md = """# A
Before
```
# Not a header
```
After
# B
Content
"""
    sections = parse_markdown_headers(md)
    assert sections == [
        ("A", "Before\n```\n# Not a header\n```\nAfter"),
        ("B", "Content"),
    ]


@pytest.mark.unit
def test_headers_inside_tilde_code_fence_are_ignored():
    md = """# A
~~~python
## Also not a header
~~~
# B
Body
"""
    sections = parse_markdown_headers(md)
    assert sections == [
        ("A", "~~~python\n## Also not a header\n~~~"),
        ("B", "Body"),
    ]


@pytest.mark.unit
def test_header_with_closing_hashes():
    md = """## Title ##
Body
"""
    sections = parse_markdown_headers(md)
    assert sections == [("Title", "Body")]


@pytest.mark.unit
def test_text_before_first_header_is_ignored():
    md = """Prelude text that should be ignored
# Header
Content
"""
    sections = parse_markdown_headers(md)
    assert sections == [("Header", "Content")]
