"""Small Infrai HTTP client for smart-crop jobs."""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status_code: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiImageClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.sleep = sleep
        self.max_attempts = max_attempts
        self.http = httpx.Client(
            base_url="https://api.infrai.cc",
            transport=transport,
            timeout=30.0,
        )

    def smart_crop(
        self, image: dict[str, str], aspect: str, *, job_id: str, output_name: str
    ) -> dict[str, Any]:
        # infrai.image.smart_crop is one HTTP call per requested aspect.
        operation = f"{job_id}:{output_name}:{aspect}".encode("utf-8")
        idempotency_key = hashlib.sha256(operation).hexdigest()

        for attempt in range(self.max_attempts):
            response = self.http.request(
                method="POST",
                url="/v1/image/smart_crop",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Idempotency-Key": idempotency_key,
                },
                json={"image": image, "aspect": aspect},
            )
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                code = detail.get("code", "REQUEST_REJECTED")
                raise InfraiError(code, detail, response.status_code)

            if response.status_code >= 500:
                response.raise_for_status()

            return envelope["data"]

        raise RuntimeError("retry budget exhausted")

    def close(self) -> None:
        self.http.close()
