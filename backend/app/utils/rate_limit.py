"""
Per-IP request limits.

In-memory sliding windows, per Cloud Run instance. They stop one client from
flooding the tracking endpoints; they are not a precise global quota.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.helpers import client_ip

# bucket -> (requests, window seconds)
LIMITS: Dict[str, Tuple[int, int]] = {
    "new_session": (30, 60),  # POST /detection/sessions
    "write": (600, 60),  # any other POST
    "ai_fix": (20, 3600),  # POST /tracking/decipher/fix (each call is a paid AI request)
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Return 429 when one IP exceeds the limits above."""

    def __init__(self, app, limits: Optional[Dict[str, Tuple[int, int]]] = None):
        super().__init__(app)
        self.limits = limits or LIMITS
        self.hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self.last_sweep = time.monotonic()

    @staticmethod
    def _bucket(request: Request) -> Optional[str]:
        if request.method != "POST":
            return None
        path = request.url.path.rstrip("/")
        if path.endswith("/detection/sessions"):
            return "new_session"
        if path.endswith("/tracking/decipher/fix"):
            return "ai_fix"
        return "write"

    async def dispatch(self, request: Request, call_next):
        bucket = self._bucket(request)
        if bucket and bucket not in self.limits:
            bucket = "write" if "write" in self.limits else None
        if bucket:
            limit, window = self.limits[bucket]
            now = time.monotonic()
            hits = self.hits[(client_ip(request) or "unknown", bucket)]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= limit:
                return JSONResponse(
                    {"detail": "Too many requests from this address. Try again shortly."},
                    status_code=429,
                    headers={"Retry-After": str(window)},
                )
            hits.append(now)
            if now - self.last_sweep > 300:
                self.last_sweep = now
                for stale in [key for key, value in self.hits.items() if not value or now - value[-1] > 600]:
                    del self.hits[stale]
        return await call_next(request)
