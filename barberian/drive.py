"""Google Drive artifact contract. Credentials are supplied by runtime configuration."""

from dataclasses import dataclass
from typing import BinaryIO, Protocol


DRIVE_FOLDERS = (
    "Projects", "Research", "Images", "Videos/Raw", "Videos/Intermediate",
    "Videos/Edited", "Videos/Final", "Audio", "Documents", "Artifacts", "Temp",
)


@dataclass(slots=True, frozen=True)
class DriveFile:
    file_id: str
    name: str
    mime_type: str
    size: int
    checksum: str | None = None
    folder_id: str | None = None


class DriveStore(Protocol):
    def upload(self, stream: BinaryIO, name: str, mime_type: str, folder_id: str) -> DriveFile: ...
    def download(self, file_id: str) -> BinaryIO: ...
    def delete(self, file_id: str) -> None: ...


def folder_plan(root: str = "AI AGENT") -> list[str]:
    return [f"{root}/{item}" for item in DRIVE_FOLDERS]
