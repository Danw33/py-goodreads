"""Unofficial asynchronous client for public Goodreads reading data."""

from .client import GoodreadsClient
from .errors import (
    GoodreadsConnectionError,
    GoodreadsError,
    GoodreadsNotFoundError,
    GoodreadsParseError,
    GoodreadsResponseError,
)
from .models import (
    GoodreadsBook,
    GoodreadsProfile,
    GoodreadsReading,
    GoodreadsShelf,
    GoodreadsShelfBook,
    GoodreadsSnapshot,
    ReadingProgress,
)
from .parsers import normalize_shelf_name, parse_user_id

__all__ = [
    "GoodreadsBook",
    "GoodreadsClient",
    "GoodreadsConnectionError",
    "GoodreadsError",
    "GoodreadsNotFoundError",
    "GoodreadsParseError",
    "GoodreadsProfile",
    "GoodreadsReading",
    "GoodreadsResponseError",
    "GoodreadsShelf",
    "GoodreadsShelfBook",
    "GoodreadsSnapshot",
    "ReadingProgress",
    "normalize_shelf_name",
    "parse_user_id",
]

__version__ = "0.1.1"
