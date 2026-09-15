"""Memory boundary separating private device data from share-safe knowledge."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class MemoryItem:
    key: str
    value: Any
    sensitivity: str = "private"
    verified: bool = False


class MemoryStore:
    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def put(self, item: MemoryItem) -> None:
        self._items[item.key] = item

    def get(self, key: str) -> MemoryItem | None:
        return self._items.get(key)

    def share_safe(self) -> list[MemoryItem]:
        return [item for item in self._items.values() if item.sensitivity == "shared-safe" and item.verified]
