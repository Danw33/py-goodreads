"""Parsers for Goodreads' public RSS surfaces."""

import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urlparse
from xml.etree import ElementTree

from .errors import GoodreadsParseError
from .models import (
    GoodreadsBook,
    GoodreadsProfile,
    GoodreadsShelf,
    GoodreadsShelfBook,
    ReadingProgress,
)

_BOOK_ID_PATTERN = re.compile(r"/book/show/(\d+)")
_PROFILE_ID_PATTERN = re.compile(r"^/user/show/(\d+)(?:[-/].*)?$")
_REVIEW_ID_PATTERN = re.compile(r"/review/show/(\d+)")
_PAGE_PROGRESS_PATTERN = re.compile(
    r"\bis on page\s+(\d+)\s+of\s+(\d+)\s+of\b", re.IGNORECASE
)
_PERCENT_PROGRESS_PATTERN = re.compile(
    r"\bis\s+(\d+(?:\.\d+)?)%\s+done with\b", re.IGNORECASE
)
_SAFE_SHELF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def parse_user_id(value: str | int) -> str:
    """Extract a numeric Goodreads user identifier from an ID or profile URL."""

    if isinstance(value, bool):
        raise ValueError("A Goodreads user ID must be numeric")
    text = str(value).strip()
    if text.isdigit():
        return text
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Enter a Goodreads user ID or profile URL")
    if parsed.hostname not in {"goodreads.com", "www.goodreads.com"}:
        raise ValueError("The profile URL must be hosted on goodreads.com")
    if match := _PROFILE_ID_PATTERN.fullmatch(parsed.path.rstrip("/")):
        return match.group(1)
    raise ValueError("The Goodreads profile URL is not supported")


def normalize_shelf_name(value: str) -> str:
    """Validate and normalize a Goodreads shelf name."""

    shelf = value.strip().lower().replace(" ", "-")
    if not _SAFE_SHELF_PATTERN.fullmatch(shelf):
        raise ValueError("The Goodreads shelf name is not supported")
    return shelf


def _text(parent: ElementTree.Element, path: str) -> str | None:
    """Return stripped element text when present."""

    value = parent.findtext(path)
    return value.strip() if value and value.strip() else None


def _parse_xml(payload: bytes) -> ElementTree.Element:
    """Parse trusted Goodreads XML while rejecting entity declarations."""

    upper_payload = payload.upper()
    if b"<!DOCTYPE" in upper_payload or b"<!ENTITY" in upper_payload:
        raise GoodreadsParseError("The Goodreads feed contains unsafe XML")
    try:
        return ElementTree.fromstring(payload)
    except ElementTree.ParseError as err:
        raise GoodreadsParseError("Goodreads returned malformed XML") from err


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an RFC 2822 timestamp used by Goodreads feeds."""

    if value is None:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError) as err:
        raise GoodreadsParseError("Goodreads returned an invalid timestamp") from err


def _parse_int(value: str | None) -> int | None:
    """Parse an optional integer."""

    if value is None:
        return None
    try:
        return int(value)
    except ValueError as err:
        raise GoodreadsParseError("Goodreads returned an invalid integer") from err


def _parse_float(value: str | None) -> float | None:
    """Parse an optional floating-point number."""

    if value is None:
        return None
    try:
        return float(value)
    except ValueError as err:
        raise GoodreadsParseError("Goodreads returned an invalid number") from err


def _profile_name(
    channel: ElementTree.Element, items: list[ElementTree.Element]
) -> str:
    """Read the profile display name from stable feed fields."""

    for item in items:
        if name := _text(item, "user_name"):
            return name
    title = _text(channel, "title")
    marker = "'s bookshelf:"
    if title and marker in title:
        return title.split(marker, maxsplit=1)[0]
    raise GoodreadsParseError("Goodreads did not identify the profile")


def parse_shelf_feed(payload: bytes, user_id: str, shelf_name: str) -> GoodreadsShelf:
    """Parse a Goodreads shelf RSS response."""

    root = _parse_xml(payload)
    channel = root.find("channel")
    if channel is None:
        raise GoodreadsParseError("Goodreads did not return an RSS channel")
    items = channel.findall("item")
    profile = GoodreadsProfile(
        user_id=user_id,
        name=_profile_name(channel, items),
        profile_url=f"https://www.goodreads.com/user/show/{user_id}",
    )
    books: list[GoodreadsShelfBook] = []
    for item in items:
        book_id = _text(item, "book_id")
        title = _text(item, "title")
        author = _text(item, "author_name")
        if not book_id or not title or not author:
            raise GoodreadsParseError("A Goodreads shelf item is missing book data")
        review_url = _text(item, "link")
        review_match = _REVIEW_ID_PATTERN.search(review_url or "")
        rating = _parse_int(_text(item, "user_rating"))
        small_cover_url = _text(item, "book_small_image_url")
        medium_cover_url = _text(item, "book_medium_image_url")
        large_cover_url = _text(item, "book_large_image_url")
        books.append(
            GoodreadsShelfBook(
                book=GoodreadsBook(
                    book_id=book_id,
                    title=title,
                    author=author,
                    url=f"https://www.goodreads.com/book/show/{book_id}",
                    cover_url=large_cover_url or medium_cover_url or small_cover_url,
                    small_cover_url=small_cover_url,
                    large_cover_url=large_cover_url,
                    isbn=_text(item, "isbn"),
                    total_pages=_parse_int(_text(item, "book/num_pages")),
                    average_rating=_parse_float(_text(item, "average_rating")),
                    published_year=_parse_int(_text(item, "book_published")),
                ),
                review_id=review_match.group(1) if review_match else None,
                review_url=review_url,
                shelves=tuple(
                    shelf.strip()
                    for shelf in (_text(item, "user_shelves") or "").split(",")
                    if shelf.strip()
                ),
                rating=rating if rating else None,
                date_added=_parse_datetime(_text(item, "user_date_added")),
                date_created=_parse_datetime(_text(item, "user_date_created")),
                read_at=_parse_datetime(_text(item, "user_read_at")),
                updated_at=_parse_datetime(_text(item, "pubDate")),
            )
        )
    return GoodreadsShelf(
        profile=profile,
        name=shelf_name,
        books=tuple(books),
        updated_at=_parse_datetime(_text(channel, "lastBuildDate")),
    )


def parse_progress_feed(payload: bytes) -> tuple[ReadingProgress, ...]:
    """Parse progress events from a Goodreads user updates RSS response."""

    root = _parse_xml(payload)
    channel = root.find("channel")
    if channel is None:
        raise GoodreadsParseError("Goodreads did not return an RSS channel")
    progress_by_book: dict[str, ReadingProgress] = {}
    for item in channel.findall("item"):
        description = unescape(_text(item, "description") or "")
        if not (book_match := _BOOK_ID_PATTERN.search(description)):
            continue
        current_page: int | None = None
        total_pages: int | None = None
        percent: float | None = None
        if page_match := _PAGE_PROGRESS_PATTERN.search(description):
            current_page = int(page_match.group(1))
            total_pages = int(page_match.group(2))
            if total_pages > 0:
                percent = current_page / total_pages * 100
        elif percent_match := _PERCENT_PROGRESS_PATTERN.search(description):
            percent = float(percent_match.group(1))
        else:
            continue
        updated_at = _parse_datetime(_text(item, "pubDate"))
        if updated_at is None:
            raise GoodreadsParseError("A Goodreads progress item has no timestamp")
        book_id = book_match.group(1)
        progress_by_book.setdefault(
            book_id,
            ReadingProgress(
                book_id=book_id,
                status_id=_text(item, "guid"),
                current_page=current_page,
                total_pages=total_pages,
                percent=percent,
                updated_at=updated_at,
            ),
        )
    return tuple(progress_by_book.values())
