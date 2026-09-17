"""Typed public models for py-goodreads."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class GoodreadsProfile:
    """A Goodreads user represented by its stable numeric identifier."""

    user_id: str
    name: str
    profile_url: str


@dataclass(frozen=True, slots=True)
class GoodreadsBook:
    """Book metadata exposed by a Goodreads shelf feed."""

    book_id: str
    title: str
    author: str
    url: str
    cover_url: str | None = None
    small_cover_url: str | None = None
    large_cover_url: str | None = None
    isbn: str | None = None
    total_pages: int | None = None
    average_rating: float | None = None
    published_year: int | None = None


@dataclass(frozen=True, slots=True)
class GoodreadsShelfBook:
    """A book together with user-specific shelf metadata."""

    book: GoodreadsBook
    review_id: str | None
    review_url: str | None
    shelves: tuple[str, ...]
    rating: int | None
    date_added: datetime | None
    date_created: datetime | None
    read_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class GoodreadsShelf:
    """One public Goodreads shelf feed."""

    profile: GoodreadsProfile
    name: str
    books: tuple[GoodreadsShelfBook, ...]
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class ReadingProgress:
    """The latest progress activity parsed for a book."""

    book_id: str
    updated_at: datetime
    status_id: str | None = None
    current_page: int | None = None
    total_pages: int | None = None
    percent: float | None = None


@dataclass(frozen=True, slots=True)
class GoodreadsReading:
    """A currently-reading shelf item enriched with recent progress."""

    shelf_book: GoodreadsShelfBook
    progress: ReadingProgress | None = None

    @property
    def book(self) -> GoodreadsBook:
        """Return book metadata."""

        return self.shelf_book.book

    @property
    def last_activity_at(self) -> datetime | None:
        """Return the newest known activity for this reading."""

        if self.progress is not None:
            return self.progress.updated_at
        return self.shelf_book.updated_at


@dataclass(frozen=True, slots=True)
class GoodreadsSnapshot:
    """Current public reading state for a Goodreads profile."""

    profile: GoodreadsProfile
    currently_reading: tuple[GoodreadsReading, ...]
    updated_at: datetime | None

    @property
    def active_reading(self) -> GoodreadsReading | None:
        """Return the current book with the newest known activity."""

        if not self.currently_reading:
            return None
        minimum = datetime.min.replace(
            tzinfo=self.updated_at.tzinfo if self.updated_at else None
        )
        return max(
            self.currently_reading,
            key=lambda reading: reading.last_activity_at or minimum,
        )
