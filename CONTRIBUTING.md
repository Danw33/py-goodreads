# Contributing

Thank you for helping improve `py-goodreads`.

## Development setup

Use Python 3.11 or newer and install the editable test environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable '.[test]'
```

Before opening a pull request, run:

```bash
ruff format --check .
ruff check .
mypy
pytest --cov=pygoodreads --cov-report=term-missing
python -m build
twine check dist/*
```

Tests must use synthetic, anonymized feed data. Do not commit cookies, account
credentials, private profiles, full production responses, or unnecessary
personal reading history. Changes should remain read-only unless write support
has first been explicitly designed and agreed.
