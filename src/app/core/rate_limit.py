"""In-process fixed-window rate limiter, keyed by API key.

One counter per key per 60-second window. This is correct for a single app
process; a multi-process or multi-host deployment should back it with Redis
behind the same `check()` interface. State is module-level so it persists across
requests within a worker.
"""

from __future__ import annotations

import time

from .errors import RateLimitedError

WINDOW_SECONDS = 60

# api_key_id -> (window_index, count_in_window)
_state: dict[str, tuple[int, int]] = {}


def check(api_key_id: str, limit: int, now: float | None = None) -> int:
    """Count one request for this key in the current window.

    Returns how many requests remain allowed in the window. Raises
    RateLimitedError (HTTP 429) once the limit has been exceeded.
    """
    now = time.time() if now is None else now
    window = int(now // WINDOW_SECONDS)
    prev_window, count = _state.get(api_key_id, (window, 0))
    count = count + 1 if prev_window == window else 1
    _state[api_key_id] = (window, count)

    if count > limit:
        retry_after = WINDOW_SECONDS - int(now % WINDOW_SECONDS)
        raise RateLimitedError(
            "Rate limit exceeded. Slow down.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )
    return max(0, limit - count)


def reset() -> None:
    """Clear all counters (used by tests)."""
    _state.clear()
