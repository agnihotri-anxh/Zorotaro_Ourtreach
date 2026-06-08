"""Http client with retries and rate-limit backoff."""
from typing import Any, Dict, Optional
import time
import json
import requests

RETRYABLE = {429, 500, 502, 503, 504}


class ApiError(Exception):
    def __init__(self, status: int, code: Optional[str], message: str, rate_headers: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{status}] {code or ''} {message}".strip())
        self.status = status
        self.code = code
        self.detail = message
        self.rate_headers = rate_headers


class HttpClient:
    def __init__(self, timeout: float = 30.0, max_retries: int = 4, sleep_func=time.sleep,
                 min_interval: float = 0.0, now_func=time.time):
        self.timeout = timeout
        self.max_retries = max_retries
        self.sleep = sleep_func
        self.min_interval = min_interval
        self.now = now_func
        self._next_allowed_at = 0.0
        self._session = requests.Session()

    def _throttle(self):
        if self.min_interval <= 0:
            return
        wait = self._next_allowed_at - self.now()
        if wait > 0:
            self.sleep(wait)
        self._next_allowed_at = self.now() + self.min_interval

    def request_json(self, method: str, url: str, *, headers: Optional[Dict[str, str]] = None,
                     body: Optional[Dict[str, Any]] = None) -> Any:
        self._throttle()
        attempt = 0
        headers = headers or {}
        while True:
            try:
                resp = self._session.request(method, url, headers=headers, json=body, timeout=self.timeout)
            except requests.RequestException as err:
                if attempt >= self.max_retries:
                    raise ApiError(0, "network_error", str(err))
                self._backoff(attempt, None)
                attempt += 1
                continue

            rate = self._rate_headers(resp)
            daily_exhausted = rate.get("dailyLeft") == "0"
            if resp.status_code in RETRYABLE and attempt < self.max_retries and not daily_exhausted:
                self._backoff(attempt, rate.get("retryAfter"))
                attempt += 1
                continue

            if resp.status_code >= 400:
                code, message = self._parse_error(resp)
                raise ApiError(resp.status_code, code, message, rate)

            text = resp.text
            if not text:
                return {}
            try:
                return resp.json()
            except ValueError:
                return {"_raw": text}

    def _backoff(self, attempt: int, retry_after: Optional[str]):
        if retry_after is not None:
            try:
                secs = float(retry_after)
                self.sleep(secs)
                return
            except Exception:
                pass
        self.sleep(min(2 ** attempt, 30))

    def _rate_headers(self, resp: requests.Response) -> Dict[str, Optional[str]]:
        g = resp.headers.get
        return {
            "retryAfter": g("Retry-After"),
            "minuteLeft": g("X-Minute-Request-Left"),
            "dailyLeft": g("X-Daily-Request-Left"),
            "dailyResetSeconds": g("X-Daily-Reset-Seconds"),
        }

    def _parse_error(self, resp: requests.Response):
        try:
            body = resp.json()
        except ValueError:
            return None, resp.text or ""
        code = body.get("code") if isinstance(body, dict) else None
        raw = body.get("message") or body.get("detail") or body
        message = raw if isinstance(raw, str) else json.dumps(raw)
        return code, message
