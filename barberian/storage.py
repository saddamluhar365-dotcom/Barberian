"""Artifact storage abstraction; database stores metadata, blobs stay in object storage."""

from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(slots=True, frozen=True)
class Artifact:
    id: str
    name: str
    mime_type: str
    size: int
    checksum: str
    storage_id: str | None = None
    project_id: str | None = None
    status: str = "ready"
    version: int = 1
    parent_id: str | None = None


class ArtifactStore(Protocol):
    def put(self, stream: BinaryIO, artifact: Artifact) -> Artifact: ...
    def get(self, storage_id: str) -> BinaryIO: ...
    def delete(self, storage_id: str) -> None: ...
