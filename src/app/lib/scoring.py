"""Address confidence + freshness scoring (pure functions).

freshness() decays with time since the address was last verified; combined_score()
blends stored confidence with freshness and a small bonus per successful
verification (the verification/delivery feedback loop, the data moat); is_stale()
flags addresses that need re-checking. All pure and unit-tested.
"""

from __future__ import annotations

from datetime import datetime

FRESH_DAYS = 30  # full freshness within this many days of the last check
DECAY_END_DAYS = 365  # freshness reaches 0 here
STALE_DAYS = 180  # flagged stale beyond this


def _age_days(reference: datetime, now: datetime) -> float:
    return (now - reference).total_seconds() / 86400.0


def freshness(reference: datetime, now: datetime) -> float:
    age = _age_days(reference, now)
    if age <= FRESH_DAYS:
        return 1.0
    if age >= DECAY_END_DAYS:
        return 0.0
    return max(0.0, 1.0 - (age - FRESH_DAYS) / (DECAY_END_DAYS - FRESH_DAYS))


def is_stale(reference: datetime, now: datetime, max_days: int = STALE_DAYS) -> bool:
    return _age_days(reference, now) > max_days


def combined_score(confidence: float, freshness_value: float, verification_count: int) -> float:
    bonus = min(0.1, 0.02 * verification_count)
    return round(min(1.0, confidence * (0.6 + 0.4 * freshness_value) + bonus), 3)
