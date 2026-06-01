"""Unit tests for the rate limiter — pure logic, no database, no app."""

import pytest

from app.core import rate_limit
from app.core.errors import RateLimitedError


def test_allows_up_to_the_limit_then_blocks():
    rate_limit.reset()
    now = 1000.0  # one fixed instant -> same window for every call
    assert rate_limit.check("k1", 3, now=now) == 2
    assert rate_limit.check("k1", 3, now=now) == 1
    assert rate_limit.check("k1", 3, now=now) == 0
    with pytest.raises(RateLimitedError):
        rate_limit.check("k1", 3, now=now)


def test_counter_resets_in_the_next_window():
    rate_limit.reset()
    now = 1000.0
    rate_limit.check("k2", 1, now=now)
    with pytest.raises(RateLimitedError):
        rate_limit.check("k2", 1, now=now)
    # A minute later the window rolls over and the budget is fresh.
    assert rate_limit.check("k2", 1, now=now + rate_limit.WINDOW_SECONDS) == 0


def test_keys_are_independent():
    rate_limit.reset()
    now = 1000.0
    rate_limit.check("a", 1, now=now)
    assert rate_limit.check("b", 1, now=now) == 0  # different key, own budget


def test_retry_after_header_present_on_block():
    rate_limit.reset()
    now = 1000.0
    rate_limit.check("k3", 1, now=now)
    with pytest.raises(RateLimitedError) as exc:
        rate_limit.check("k3", 1, now=now)
    assert "Retry-After" in exc.value.headers
