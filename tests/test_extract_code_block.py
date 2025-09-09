import pytest

from aipg.prompting.utils import extract_code_block


@pytest.mark.unit
@pytest.mark.parametrize(
    "text,prefer_languages,expected",
    [
        (
            """
Intro
```python
print('hello')
```
Outro
""",
            None,
            "print('hello')",
        ),
        (
            """
```js
console.log('x')
```
---
```python
print('y')
```
""",
            ["python"],
            "print('y')",
        ),
        (
            """
```js
console.log('x')
```
---
```python
print('y')
```
""",
            ["go"],
            None,
        ),
        (
            """
```js
console.log('x')
```
---
```python
print('y')
```
""",
            None,
            "console.log('x')",
        ),
        (
            """
# Header
```js
console.log('x')
```
## Header 2
```python
print('y')
```
""",
            None,
            "console.log('x')",
        ),
        (
            """
No fenced blocks here.
Just plain text.
""",
            None,
            None,
        ),
        (
            """
# Header
```
console.log('x')
```
## Header 2
```python
print('y')
```
""",
            None,
            "console.log('x')",
        ),
    ],
)
def test_extract_code_block_main_paths(text, prefer_languages, expected):
    result = extract_code_block(
        text,
        prefer_languages=prefer_languages,
        return_fenced=False,
        strip_trailing_newlines=True,
    )

    assert result == expected
