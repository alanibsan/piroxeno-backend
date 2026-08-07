import time
from collections import defaultdict, deque

from fastapi import HTTPException


_requests = defaultdict(deque)


def check_rate_limit(key: str, limit: int, window_seconds: int = 60):
    now = time.time()
    bucket = _requests[key]

    while bucket and bucket[0] <= now - window_seconds:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    bucket.append(now)
