"""Small HTTP client for the existing FastAPI application."""

import os
from typing import Any

import requests


class APIError(RuntimeError):
    """A readable error returned by the backend or network layer."""


class CaptionAPI:
    def __init__(self, base_url: str | None = None, timeout: tuple[int, int] = (10, 120)):
        self.base_url = (base_url or os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    @staticmethod
    def _raise_for_response(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            message: Any = None
            try:
                body = response.json()
                message = body.get("detail", body)
            except ValueError:
                message = response.text.strip()
            if isinstance(message, (dict, list)):
                message = str(message)
            raise APIError(message or f"Backend returned HTTP {response.status_code}.") from exc

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
        except requests.Timeout as exc:
            raise APIError("The backend took too long to respond. Please try again.") from exc
        except requests.ConnectionError as exc:
            raise APIError("Could not connect to the backend. Check that FastAPI is running.") from exc
        except requests.RequestException as exc:
            raise APIError(f"Backend request failed: {exc}") from exc
        self._raise_for_response(response)
        return response

    def generate_captions(
        self,
        image_bytes: bytes,
        filename: str,
        platform: str,
        language: str,
        style: str,
        template: str,
    ) -> dict[str, Any]:
        """Call the combined BLIP and Groq generation endpoint once."""
        mime_type = self._mime_type(filename)
        response = self._request(
            "POST",
            "/api/v1/generate/",
            files={"file": (filename, image_bytes, mime_type)},
            data={
                "platform": platform,
                "language": language,
                "style": style,
                "template": template,
            },
        )
        try:
            result = response.json()
        except ValueError as exc:
            raise APIError("The backend returned an unreadable generation response.") from exc
        if not isinstance(result, dict) or not result.get("base_caption") or not result.get("generated_caption"):
            raise APIError("The backend response did not include both captions.")
        return result

    def render_captioned_image(
        self,
        image_bytes: bytes,
        filename: str,
        caption: str,
        language: str,
        template: str,
    ) -> bytes:
        """Request a PNG from the existing Pillow rendering endpoint."""
        response = self._request(
            "POST",
            "/api/v1/image/captioned",
            files={"file": (filename, image_bytes, self._mime_type(filename))},
            data={
                "caption": caption,
                "language": language,
                "template": template,
                "canvas_preset": "original",
            },
        )
        if not response.headers.get("content-type", "").lower().startswith("image/png"):
            raise APIError("The backend did not return a PNG image.")
        return response.content

    def list_history(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        response = self._request(
            "GET", "/api/v1/history/", params={"limit": limit, "offset": offset}
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise APIError("The backend returned an unreadable history response.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
            raise APIError("The backend history response has an unexpected format.")
        return payload

    def get_history_record(self, record_id: int) -> dict[str, Any]:
        response = self._request("GET", f"/api/v1/history/{int(record_id)}")
        try:
            return response.json()
        except ValueError as exc:
            raise APIError("The backend returned an unreadable history record.") from exc

    def delete_history_record(self, record_id: int) -> None:
        self._request("DELETE", f"/api/v1/history/{int(record_id)}")

    @staticmethod
    def _mime_type(filename: str) -> str:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }.get(extension, "application/octet-stream")
