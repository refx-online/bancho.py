from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any
from typing import TypedDict


class Message(TypedDict):
    type: str
    pattern: str | None
    channel: bytes
    data: bytes | Any


PUBSUB_HANDLER = Callable[[str], Awaitable[None]]
