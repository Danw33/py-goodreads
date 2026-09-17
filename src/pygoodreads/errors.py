"""Exceptions raised by py-goodreads."""


class GoodreadsError(Exception):
    """Base exception for all Goodreads client errors."""


class GoodreadsConnectionError(GoodreadsError):
    """The Goodreads service could not be reached."""


class GoodreadsResponseError(GoodreadsError):
    """Goodreads returned an unsuccessful or unsupported response."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        """Initialize a response error."""

        super().__init__(message)
        self.status = status


class GoodreadsNotFoundError(GoodreadsResponseError):
    """The requested Goodreads profile or feed does not exist."""


class GoodreadsParseError(GoodreadsResponseError):
    """A Goodreads feed could not be parsed safely."""
