"""Per-export state.

Everything that used to live in module globals or on discord.py classes (the lookup cache, the dropdown
counter, the timezone and the bot) is kept here instead, so concurrent exports cannot interfere with
each other.
"""

import contextlib
import contextvars
from typing import Any, Optional

import aiohttp

HTTP_TIMEOUT = aiohttp.ClientTimeout(total=10, connect=5)


class ExportState:
    def __init__(self, timezone: str = "UTC", bot: Any = None):
        self.cache: dict = {}
        self.menu_div_id = 0
        self.timezone = timezone
        self.bot = bot
        self._session: Optional[aiohttp.ClientSession] = None

    def http_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=HTTP_TIMEOUT)
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None


# Used when library helpers are called outside of an export (e.g. ParseMarkdown in tests).
_default_state = ExportState()
_current: contextvars.ContextVar = contextvars.ContextVar("chat_exporter_state", default=None)


def current() -> ExportState:
    return _current.get() or _default_state


def in_export() -> bool:
    return _current.get() is not None


@contextlib.asynccontextmanager
async def export_scope(timezone: str = "UTC", bot: Any = None):
    state = ExportState(timezone=timezone, bot=bot)
    token = _current.set(state)
    try:
        yield state
    finally:
        _current.reset(token)
        await state.close()


@contextlib.asynccontextmanager
async def http_session():
    """Shared session inside an export; a short-lived one otherwise."""
    if in_export():
        yield current().http_session()
        return
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        yield session
