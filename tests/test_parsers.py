"""Tests for Goodreads feed and identifier parsing."""

from datetime import datetime

import pytest

from pygoodreads import GoodreadsParseError, normalize_shelf_name, parse_user_id
from pygoodreads.parsers import parse_progress_feed, parse_shelf_feed

from .conftest import SHELF_XML, UPDATES_XML


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("12345", "12345"),
        (12345, "12345"),
        (" https://www.goodreads.com/user/show/12345-alex ", "12345"),
        ("http://goodreads.com/user/show/12345/", "12345"),
    ],
)
def test_parse_user_id(value: str | int, expected: str) -> None:
    """Accept stable IDs and ordinary Goodreads profile URLs."""

    assert parse_user_id(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        True,
        "alex",
        "ftp://www.goodreads.com/user/show/12345",
        "https://example.com/user/show/12345",
        "https://www.goodreads.com/book/show/12345",
    ],
)
def test_parse_user_id_rejects_unsupported_values(value: object) -> None:
    """Reject ambiguous and non-Goodreads values."""

    with pytest.raises(ValueError):
        parse_user_id(value)  # type: ignore[arg-type]


def test_normalize_shelf_name() -> None:
    """Normalize common shelf input and reject unsafe path data."""

    assert normalize_shelf_name(" Want To Read ") == "want-to-read"
    with pytest.raises(ValueError):
        normalize_shelf_name("../private")


def test_parse_shelf_feed() -> None:
    """Parse book and user metadata from a real-shaped shelf feed."""

    shelf = parse_shelf_feed(SHELF_XML, "42", "currently-reading")
    item = shelf.books[0]
    assert shelf.profile.user_id == "42"
    assert shelf.profile.name == "Alex"
    assert shelf.profile.profile_url.endswith("/42")
    assert shelf.updated_at == datetime.fromisoformat("2026-09-15T17:08:38+00:00")
    assert item.book.book_id == "123"
    assert item.book.title == "Example Book"
    assert item.book.author == "Casey Writer"
    assert item.book.total_pages == 320
    assert item.book.average_rating == 4.25
    assert item.book.published_year == 2026
    assert item.book.cover_url == "https://images.example/large.jpg"
    assert item.review_id == "456"
    assert item.rating is None
    assert item.shelves == ("currently-reading", "favourites")
    assert item.date_added is not None
    assert item.date_created is not None
    assert item.read_at is None


def test_parse_shelf_name_falls_back_to_title() -> None:
    """Use the feed title when an empty shelf has no item user name."""

    payload = b"""<rss><channel><title>Sam's bookshelf: read</title></channel></rss>"""
    assert parse_shelf_feed(payload, "7", "read").profile.name == "Sam"


def test_parse_progress_feed() -> None:
    """Keep the newest page or percentage event for each book."""

    progress = parse_progress_feed(UPDATES_XML)
    assert len(progress) == 2
    assert progress[0].book_id == "123"
    assert progress[0].status_id == "UserStatus999"
    assert progress[0].current_page == 80
    assert progress[0].total_pages == 320
    assert progress[0].percent == 25
    assert progress[1].book_id == "789"
    assert progress[1].percent == 42.5
    assert progress[1].current_page is None


@pytest.mark.parametrize(
    "payload",
    [
        b"<not-rss />",
        b"not xml",
        b"<!DOCTYPE rss [<!ENTITY example 'unsafe'>]><rss />",
        b"<rss><channel><item><book_id>1</book_id></item></channel></rss>",
        b"<rss><channel><title>Unknown feed</title></channel></rss>",
        b"<rss><channel><title>A's bookshelf: read</title><lastBuildDate>bad</lastBuildDate></channel></rss>",
    ],
)
def test_parse_shelf_rejects_invalid_feeds(payload: bytes) -> None:
    """Turn malformed and unsupported XML into a stable library error."""

    with pytest.raises(GoodreadsParseError):
        parse_shelf_feed(payload, "1", "read")


def test_parse_shelf_rejects_invalid_numbers() -> None:
    """Reject malformed numeric metadata."""

    payload = SHELF_XML.replace(b"<num_pages>320", b"<num_pages>many")
    with pytest.raises(GoodreadsParseError):
        parse_shelf_feed(payload, "1", "currently-reading")
    payload = SHELF_XML.replace(b"<average_rating>4.25", b"<average_rating>great")
    with pytest.raises(GoodreadsParseError):
        parse_shelf_feed(payload, "1", "currently-reading")


def test_parse_progress_rejects_invalid_feed() -> None:
    """Require an RSS channel and valid timestamps for progress."""

    with pytest.raises(GoodreadsParseError):
        parse_progress_feed(b"<rss />")
    payload = UPDATES_XML.replace(b"Tue, 15 Sep 2026 17:08:38 +0000", b"invalid", 1)
    with pytest.raises(GoodreadsParseError):
        parse_progress_feed(payload)


def test_parse_page_progress_with_zero_total() -> None:
    """Preserve source page values without dividing by zero."""

    payload = UPDATES_XML.replace(b"page 80 of 320", b"page 0 of 0", 1)
    assert parse_progress_feed(payload)[0].percent is None
