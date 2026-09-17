"""Asynchronous client for Goodreads' public reading feeds."""

import asyncio
from collections.abc import Mapping
from datetime import datetime
from http import HTTPStatus
from typing import Final

from aiohttp import ClientError, ClientSession, ClientTimeout
from yarl import URL

from .errors import (
    GoodreadsConnectionError,
    GoodreadsNotFoundError,
    GoodreadsResponseError,
)
from .models import GoodreadsReading, GoodreadsShelf, GoodreadsSnapshot, ReadingProgress
from .parsers import (
    normalize_shelf_name,
    parse_progress_feed,
    parse_shelf_feed,
    parse_user_id,
)

BASE_URL: Final = URL("https://www.goodreads.com")
DEFAULT_TIMEOUT: Final = 15.0
MAX_RESPONSE_SIZE: Final = 5 * 1024 * 1024
USER_AGENT: Final = "py-goodreads/0.1.1"


class GoodreadsClient:
    """Read public Goodreads shelves and progress using an injected web session."""

    def __init__(
        self,
        session: ClientSession,
        *,
        base_url: str | URL = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the client without taking ownership of the session."""

        self._session = session
        self._base_url = URL(base_url)
        self._timeout = ClientTimeout(total=timeout)

    async def _async_get_xml(
        self, path: str, *, params: Mapping[str, str] | None = None
    ) -> bytes:
        """Fetch one bounded XML response."""

        try:
            async with self._session.get(
                self._base_url.join(URL(path)),
                params=params,
                headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml"},
                timeout=self._timeout,
            ) as response:
                if response.status == HTTPStatus.NOT_FOUND:
                    raise GoodreadsNotFoundError(
                        "The Goodreads feed was not found", status=response.status
                    )
                if response.status >= HTTPStatus.BAD_REQUEST:
                    raise GoodreadsResponseError(
                        f"Goodreads returned HTTP {response.status}",
                        status=response.status,
                    )
                payload = await response.content.read(MAX_RESPONSE_SIZE + 1)
        except GoodreadsResponseError:
            raise
        except (TimeoutError, ClientError) as err:
            raise GoodreadsConnectionError("Unable to connect to Goodreads") from err
        if len(payload) > MAX_RESPONSE_SIZE:
            raise GoodreadsResponseError(
                "The Goodreads response was unexpectedly large"
            )
        return payload

    async def async_get_shelf(
        self, user: str | int, shelf: str = "currently-reading"
    ) -> GoodreadsShelf:
        """Return one public shelf sorted by its most recent update."""

        user_id = parse_user_id(user)
        shelf_name = normalize_shelf_name(shelf)
        payload = await self._async_get_xml(
            f"/review/list_rss/{user_id}",
            params={"shelf": shelf_name, "sort": "date_updated", "order": "d"},
        )
        return parse_shelf_feed(payload, user_id, shelf_name)

    async def async_get_reading_progress(
        self, user: str | int
    ) -> tuple[ReadingProgress, ...]:
        """Return each book's latest progress event from public updates."""

        user_id = parse_user_id(user)
        payload = await self._async_get_xml(f"/user/updates_rss/{user_id}")
        return parse_progress_feed(payload)

    async def async_get_reading_snapshot(self, user: str | int) -> GoodreadsSnapshot:
        """Return currently-reading books enriched with the latest progress."""

        user_id = parse_user_id(user)
        shelf, progress_updates = await asyncio.gather(
            self.async_get_shelf(user_id),
            self.async_get_reading_progress(user_id),
        )
        progress_by_book = {progress.book_id: progress for progress in progress_updates}
        readings = tuple(
            GoodreadsReading(
                shelf_book=shelf_book,
                progress=progress_by_book.get(shelf_book.book.book_id),
            )
            for shelf_book in shelf.books
        )
        progress_updated_at = max(
            (progress.updated_at for progress in progress_updates), default=None
        )
        timestamps = tuple(
            timestamp
            for timestamp in (shelf.updated_at, progress_updated_at)
            if timestamp is not None
        )
        updated_at: datetime | None = max(timestamps, default=None)
        return GoodreadsSnapshot(
            profile=shelf.profile,
            currently_reading=readings,
            updated_at=updated_at,
        )
