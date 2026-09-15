"""Optional Google Drive transport. Imports are lazy so the core agent stays lightweight."""

from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO

from .drive import DriveFile


@dataclass(slots=True)
class GoogleDriveConfig:
    credentials_json: str
    root_folder_id: str


class GoogleDriveStore:
    def __init__(self, config: GoogleDriveConfig) -> None:
        if not config.credentials_json or not config.root_folder_id:
            raise ValueError("credentials_json and root_folder_id are required")
        self.config = config
        self._service = None

    def _service_client(self):
        if self._service is not None:
            return self._service
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError("google-api-python-client and google-auth are required for Drive transport") from exc
        credentials = Credentials.from_service_account_info(__import__("json").loads(self.config.credentials_json), scopes=["https://www.googleapis.com/auth/drive"])
        self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    def upload(self, stream: BinaryIO, name: str, mime_type: str, folder_id: str | None = None) -> DriveFile:
        try:
            from googleapiclient.http import MediaIoBaseUpload
        except ImportError as exc:
            raise RuntimeError("google-api-python-client is required for Drive transport") from exc
        data = stream.read()
        media = MediaIoBaseUpload(BytesIO(data), mimetype=mime_type, resumable=True)
        body = {"name": name, "mimeType": mime_type, "parents": [folder_id or self.config.root_folder_id]}
        item = self._service_client().files().create(body=body, media_body=media, fields="id,name,mimeType,size,parents,md5Checksum").execute()
        return DriveFile(item["id"], item["name"], item.get("mimeType", mime_type), int(item.get("size", len(data))), item.get("md5Checksum"), (item.get("parents") or [None])[0])

    def download(self, file_id: str) -> BinaryIO:
        from googleapiclient.http import MediaIoBaseDownload
        buffer = BytesIO()
        request = self._service_client().files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer

    def delete(self, file_id: str) -> None:
        self._service_client().files().delete(fileId=file_id).execute()
