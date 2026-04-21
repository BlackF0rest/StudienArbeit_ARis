from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self.hits: dict[str, deque[datetime]] = defaultdict(deque)

    def allow(self, key: str) -> tuple[bool, int]:
        now = datetime.now(timezone.utc)
        bucket = self.hits[key]

        while bucket and (now - bucket[0]) > self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            retry_after = int((self.window - (now - bucket[0])).total_seconds())
            return False, max(retry_after, 1)

        bucket.append(now)
        return True, 0
