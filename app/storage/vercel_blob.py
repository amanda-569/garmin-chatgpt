from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class BlobStorageError(RuntimeError):
    pass


class VercelBlobTokenStore:
    API_URL = "https://vercel.com/api/blob"
    API_VERSION = "12"

    def __init__(
        self,
        store_id: str,
        read_write_token: str,
        blob_path: str,
    ) -> None:
        self.store_id = self._normalize_store_id(store_id)
        self.read_write_token = read_write_token
        self.blob_path = blob_path

    @staticmethod
    def _normalize_store_id(
        store_id: str,
    ) -> str:
        if store_id.startswith("store_"):
            return store_id.removeprefix("store_")

        return store_id

    def download_to(
        self,
        destination: Path,
    ) -> None:
        encoded_path = quote(
            self.blob_path,
            safe="/",
        )

        blob_url = (
            f"https://{self.store_id}"
            f".private.blob.vercel-storage.com/"
            f"{encoded_path}?cache=0"
        )

        request = Request(
            blob_url,
            method="GET",
            headers={
                "Authorization": (f"Bearer {self.read_write_token}"),
            },
        )

        token_data = self._send_request(
            request=request,
            action="download Garmin tokens",
        )

        try:
            json.loads(token_data)
        except json.JSONDecodeError as error:
            raise BlobStorageError(
                "Downloaded Garmin token blob " "was not valid JSON."
            ) from error

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_bytes(token_data)

        os.chmod(destination, 0o600)

    def upload_from(
        self,
        source: Path,
    ) -> None:
        if not source.exists():
            raise BlobStorageError(f"Garmin token file does not exist: " f"{source}")

        token_data = source.read_bytes()

        try:
            json.loads(token_data)
        except json.JSONDecodeError as error:
            raise BlobStorageError(
                "Local Garmin token file was not " "valid JSON."
            ) from error

        query = urlencode(
            {
                "pathname": self.blob_path,
            }
        )

        request_id = (
            f"{self.store_id}:" f"{int(time.time() * 1000)}:" f"{uuid.uuid4().hex}"
        )

        request = Request(
            f"{self.API_URL}/?{query}",
            data=token_data,
            method="PUT",
            headers={
                "Authorization": (f"Bearer {self.read_write_token}"),
                "Content-Type": "application/json",
                "x-api-version": self.API_VERSION,
                "x-api-blob-request-id": request_id,
                "x-api-blob-request-attempt": "0",
                "x-vercel-blob-store-id": (self.store_id),
                "x-vercel-blob-access": "private",
                "x-add-random-suffix": "0",
                "x-allow-overwrite": "1",
                "x-content-type": "application/json",
            },
        )

        self._send_request(
            request=request,
            action="upload Garmin tokens",
        )

    @staticmethod
    def _send_request(
        request: Request,
        action: str,
    ) -> bytes:
        try:
            with urlopen(
                request,
                timeout=30,
            ) as response:
                return response.read()

        except HTTPError as error:
            error_body = error.read().decode(
                "utf-8",
                errors="replace",
            )

            raise BlobStorageError(
                f"Failed to {action}. "
                f"Vercel Blob returned HTTP "
                f"{error.code}: {error_body}"
            ) from error

        except URLError as error:
            raise BlobStorageError(f"Failed to {action}: " f"{error.reason}") from error
