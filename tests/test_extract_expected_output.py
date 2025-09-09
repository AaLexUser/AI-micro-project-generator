import pytest

from aipg.prompting.utils import extract_expected_output


@pytest.mark.unit
@pytest.mark.parametrize(
    "text,expected",
    [
        (
            """
Prelude text
```markdown
# Header
print('hello')
## Header 2
print('world')
```
After text
""",
            "# Header\nprint('hello')\n## Header 2\nprint('world')",
        ),
(
            """
Prelude text
````markdown
# Header
```python
print('hello')
```
## Header 2
```python
print('world')
```
````
After text
""",
            "# Header\nprint('hello')\n## Header 2\nprint('world')",
        ),
        (
            """
```js
console.log('x')
```
""",
            "console.log('x')",
        ),
        (
            "  Just plain text without fences  ",
            "Just plain text without fences",
        ),
        (
            """
# Header
```python
print('second')
```
## Header 2

""",
            "# Header\nprint('second')\n## Header 2",
        ),
(
           """
````
# Header
```python
print('second')
```
## Header 2
````

""",
            "# Header\nprint('second')\n## Header 2",
        ),
        (
            "",
            "",
        ),
    ],
)
def test_extract_expected_output_main_paths(text, expected):
    result = extract_expected_output(text)
    assert result == expected


