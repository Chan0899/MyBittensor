from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import requests


@dataclass
class HttpClient:
    timeout_sec: int
    max_retries: int
    min_interval_sec: float
    cache_dir: str

    def __post_init__(self) -> None:
        self._session = requests.Session()
        self._last_request_at = 0.0
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def get_json(
        self,
        url: str,
        cache_key: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict:
        if cache_key:
            cache_file = Path(self.cache_dir) / f"{cache_key}.json"
            if cache_file.exists():
                return json.loads(cache_file.read_text(encoding="utf-8"))

        attempt = 0
        last_error = None
        while attempt < self.max_retries:
            attempt += 1
            self._respect_rate_limit()
            try:
                response = self._session.get(url, timeout=self.timeout_sec, headers=headers)
                response.raise_for_status()
                payload = response.json()
                if cache_key:
                    cache_file = Path(self.cache_dir) / f"{cache_key}.json"
                    cache_file.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                return payload
            except requests.HTTPError as exc:
                response = exc.response
                if response is not None:
                    status_code = response.status_code
                    if status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                time.sleep(float(retry_after))
                            except ValueError:
                                time.sleep(min(2 ** attempt, 8))
                        else:
                            time.sleep(min(2 ** attempt, 8))
                    elif 400 <= status_code < 500:
                        raise RuntimeError(f"GET {url} failed after retries: {exc}") from exc
                    else:
                        time.sleep(min(2 ** attempt, 8))
                last_error = exc
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(min(2 ** attempt, 8))

        raise RuntimeError(f"GET {url} failed after retries: {last_error}")

    def get_text(self, url: str) -> str:
        attempt = 0
        last_error = None
        while attempt < self.max_retries:
            attempt += 1
            self._respect_rate_limit()
            try:
                response = self._session.get(url, timeout=self.timeout_sec)
                response.raise_for_status()
                return response.text
            except requests.HTTPError as exc:
                response = exc.response
                if response is not None:
                    status_code = response.status_code
                    if status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                time.sleep(float(retry_after))
                            except ValueError:
                                time.sleep(min(2 ** attempt, 8))
                        else:
                            time.sleep(min(2 ** attempt, 8))
                    elif 400 <= status_code < 500:
                        raise RuntimeError(f"GET {url} failed after retries: {exc}") from exc
                    else:
                        time.sleep(min(2 ** attempt, 8))
                last_error = exc
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(min(2 ** attempt, 8))

        raise RuntimeError(f"GET {url} failed after retries: {last_error}")

    def _respect_rate_limit(self) -> None:
        delta = time.time() - self._last_request_at
        if delta < self.min_interval_sec:
            time.sleep(self.min_interval_sec - delta)
        self._last_request_at = time.time()
