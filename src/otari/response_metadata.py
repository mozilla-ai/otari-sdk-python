"""Per-request response metadata wrappers for the Otari SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class OtariResponse(Generic[_T]):
    """A non-streaming response paired with its Otari request identifier."""

    data: _T
    request_id: str | None


class OtariStream(Generic[_T]):
    """A synchronous response stream with metadata for its individual request.

    ``request_id`` is populated when iteration opens the HTTP response, before
    the first event is yielded. It is therefore ``None`` before iteration starts.
    """

    def __init__(self, iterator_factory: Callable[[OtariStream[_T]], Iterator[_T]]) -> None:
        self.request_id: str | None = None
        self._iterator = iterator_factory(self)

    def __iter__(self) -> OtariStream[_T]:
        return self

    def __next__(self) -> _T:
        return next(self._iterator)

    def close(self) -> None:
        """Close the underlying response stream."""
        close = getattr(self._iterator, "close", None)
        if close is not None:
            close()

    def _set_request_id(self, request_id: str | None) -> None:
        self.request_id = request_id


class AsyncOtariStream(Generic[_T]):
    """An asynchronous response stream with metadata for its individual request.

    ``request_id`` is populated when iteration opens the HTTP response, before
    the first event is yielded. It is therefore ``None`` before iteration starts.
    """

    def __init__(
        self,
        iterator_factory: Callable[[AsyncOtariStream[_T]], AsyncIterator[_T]],
    ) -> None:
        self.request_id: str | None = None
        self._iterator = iterator_factory(self)

    def __aiter__(self) -> AsyncOtariStream[_T]:
        return self

    async def __anext__(self) -> _T:
        return await self._iterator.__anext__()

    async def aclose(self) -> None:
        """Close the underlying response stream."""
        close = getattr(self._iterator, "aclose", None)
        if close is not None:
            await close()

    def _set_request_id(self, request_id: str | None) -> None:
        self.request_id = request_id
