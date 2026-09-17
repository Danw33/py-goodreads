"""Tests for the asynchronous Goodreads client."""

from collections.abc import Mapping
from types import TracebackType
from typing import Any, cast

import pytest
from aiohttp import ClientConnectionError, ClientSession

from pygoodreads import (
    GoodreadsClient,
    GoodreadsConnectionError,
    GoodreadsNotFoundError,
    GoodreadsResponseError,
)

from .conftest import SHELF_XML, UPDATES_XML


class _FakeContent:
    """Provide the bounded stream read used by the client."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    async def read(self, size: int) -> bytes:
        """Return at most the requested number of bytes."""

        return self._body[:size]


class _FakeResponse:
    """Act as an aiohttp response context manager."""

    def __init__(self, body: bytes = b"", status: int = 200) -> None:
        self.status = status
        self.content = _FakeContent(body)

    async def __aenter__(self) -> "_FakeResponse":
        """Enter the request context."""

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the request context."""


class _FakeSession:
    """Route request paths to deterministic feed responses."""

    def __init__(self, responses: Mapping[str, _FakeResponse]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, Mapping[str, str] | None, dict[str, Any]]] = []

    def get(
        self,
        url: object,
        *,
        params: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> _FakeResponse:
        """Return the configured response for a request path."""

        path = str(url).removeprefix("https://example.test")
        self.calls.append((path, params, kwargs))
        return self._responses[path]


def _client(
    responses: Mapping[str, _FakeResponse],
) -> tuple[GoodreadsClient, _FakeSession]:
    """Return a client using a typed fake aiohttp session."""

    session = _FakeSession(responses)
    return (
        GoodreadsClient(cast(ClientSession, session), base_url="https://example.test"),
        session,
    )


async def test_get_shelf_progress_and_snapshot() -> None:
    """Fetch both public feed families and combine matching progress."""

    client, session = _client(
        {
            "/review/list_rss/42": _FakeResponse(SHELF_XML),
            "/user/updates_rss/42": _FakeResponse(UPDATES_XML),
        }
    )
    shelf = await client.async_get_shelf("42")
    progress = await client.async_get_reading_progress("42")
    snapshot = await client.async_get_reading_snapshot("42")

    assert shelf.books[0].book.title == "Example Book"
    assert progress[0].current_page == 80
    assert snapshot.currently_reading[0].progress == progress[0]
    assert snapshot.active_reading == snapshot.currently_reading[0]
    assert snapshot.updated_at == progress[0].updated_at
    assert snapshot.active_reading.book.title == "Example Book"
    assert session.calls[0][1] == {
        "shelf": "currently-reading",
        "sort": "date_updated",
        "order": "d",
    }
    assert session.calls[0][2]["headers"]["Accept"] == "application/rss+xml"


async def test_empty_snapshot_has_no_active_reading() -> None:
    """Represent a valid empty currently-reading shelf."""

    empty_shelf = b"""<rss><channel><title>Alex's bookshelf: currently-reading</title></channel></rss>"""
    empty_updates = b"<rss><channel><title>Alex's Updates</title></channel></rss>"
    client, _ = _client(
        {
            "/review/list_rss/42": _FakeResponse(empty_shelf),
            "/user/updates_rss/42": _FakeResponse(empty_updates),
        }
    )
    snapshot = await client.async_get_reading_snapshot("42")
    assert snapshot.active_reading is None
    assert snapshot.updated_at is None


@pytest.mark.parametrize(
    ("status", "error"),
    [(404, GoodreadsNotFoundError), (429, GoodreadsResponseError)],
)
async def test_http_errors(status: int, error: type[Exception]) -> None:
    """Map HTTP errors to stable client exceptions."""

    client, _ = _client({"/review/list_rss/42": _FakeResponse(status=status)})
    with pytest.raises(error) as raised:
        await client.async_get_shelf("42")
    assert raised.value.status == status


async def test_rejects_oversized_response() -> None:
    """Bound memory used by unexpectedly large upstream responses."""

    client, _ = _client(
        {"/review/list_rss/42": _FakeResponse(b"x" * (5 * 1024 * 1024 + 1))}
    )
    with pytest.raises(GoodreadsResponseError):
        await client.async_get_shelf("42")


async def test_connection_error() -> None:
    """Map client connection failures to a stable exception."""

    class FailingSession:
        """Raise before a response is available."""

        def get(self, *args: object, **kwargs: object) -> None:
            raise ClientConnectionError

    client = GoodreadsClient(cast(ClientSession, FailingSession()))
    with pytest.raises(GoodreadsConnectionError):
        await client.async_get_shelf("42")
