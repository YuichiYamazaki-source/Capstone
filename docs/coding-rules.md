# Python Coding Rules (enforced by Ruff)

All Python code must pass `ruff check` and `ruff format` before commit.
Configuration: `pyproject.toml`

## Style

- Line length: 88 characters max
- Quotes: double quotes (`"string"`)
- Indent: 4 spaces
- Imports: sorted by isort (stdlib → third-party → local `app.*`)

## Docstrings (Google style)

- All public functions and classes must have docstrings
- Format: one-line summary, then `Args:` / `Returns:` / `Raises:` sections
- Exception: `__init__.py`, module-level, and `__init__` methods are exempt

Example:

```python
def get_courses(query: str, limit: int = 5) -> list[dict]:
    """Search courses by keyword using hybrid search.

    Args:
        query: Search keyword or phrase.
        limit: Maximum number of results to return.

    Returns:
        List of course dictionaries with title, description, and score.
    """
```

## Type Hints

- All function signatures must have type hints (args + return)
- Use modern syntax: `str | None` (not `Optional[str]`), `list[str]` (not `List[str]`)

## Complexity

- Max cyclomatic complexity per function: 10
- If a function exceeds this, split it into smaller functions

## Verification

- After writing Python code, run: `ruff check <file>` and `ruff format <file>`
- Fix all errors before committing
