# py-goodreads

`py-goodreads` is an unofficial, fully asynchronous Python client for public
Goodreads reading data. It uses Goodreads' public RSS feeds rather than the
retired developer API and does not require credentials, cookies, or an API key.

> [!IMPORTANT]
> This project is not affiliated with Goodreads or Amazon. The feeds are
> undocumented and may change without notice. Use a conservative polling
> interval and comply with the Goodreads terms that apply to you.

## Status

The initial `0.1.0` release supports:

- numeric user IDs and ordinary Goodreads profile URLs;
- any public shelf exposed by `review/list_rss`;
- currently-reading books and book metadata;
- page-based and percentage-based progress from public user updates;
- selection of the most recently active current book;
- injected `aiohttp.ClientSession` instances for efficient connection reuse;
- Python 3.11 through 3.14 with complete type information.

Authentication, private web scraping, and write operations are intentionally
out of scope for the first release.

## Installation

The distribution name is `py-goodreads`; the import package is `pygoodreads`.

```bash
python -m pip install py-goodreads
```

## Usage

```python
import asyncio

from aiohttp import ClientSession
from pygoodreads import GoodreadsClient


async def main() -> None:
    async with ClientSession() as session:
        client = GoodreadsClient(session)
        snapshot = await client.async_get_reading_snapshot(
            "https://www.goodreads.com/user/show/12345678-reader"
        )

        print(snapshot.profile.name)
        for reading in snapshot.currently_reading:
            print(reading.book.title, reading.progress)


asyncio.run(main())
```

Read another shelf with `async_get_shelf`:

```python
read_shelf = await client.async_get_shelf("12345678", "read")
want_to_read = await client.async_get_shelf("12345678", "to-read")
```

Goodreads currently limits feed history, so a returned shelf should not be
treated as an authoritative lifetime count for large shelves.

## Data model

`GoodreadsSnapshot.currently_reading` is always a tuple because Goodreads users
can have more than one current book. Each `GoodreadsReading` combines the shelf
record with the latest matching public progress event. `active_reading` is the
book with the newest progress or shelf activity, which is useful for dashboards
that have room for a single book.

Progress preserves source values:

- page updates expose `current_page`, `total_pages`, and a derived `percent`;
- percentage updates expose `percent` while page values remain `None`;
- books without a public progress update have `progress=None`.

## Development

```bash
python -m pip install --editable '.[test]'
ruff format --check .
ruff check .
mypy
pytest --cov=pygoodreads --cov-report=term-missing
python -m build
twine check dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and
[SECURITY.md](SECURITY.md) for responsible disclosure.

## License

Copyright © 2026 Daniel Wilson ([@Danw33](https://github.com/Danw33))

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). 

Goodreads and Amazon are trademarks of their respective owners