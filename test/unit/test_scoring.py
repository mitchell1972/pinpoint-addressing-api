from datetime import UTC, datetime, timedelta

from app.lib import scoring

NOW = datetime(2026, 6, 1, tzinfo=UTC)


def test_freshness_full_when_recent():
    assert scoring.freshness(NOW - timedelta(days=5), NOW) == 1.0


def test_freshness_decays_to_zero_far_out():
    assert scoring.freshness(NOW - timedelta(days=400), NOW) == 0.0
    mid = scoring.freshness(NOW - timedelta(days=197), NOW)
    assert 0.0 < mid < 1.0


def test_is_stale_past_threshold():
    assert scoring.is_stale(NOW - timedelta(days=200), NOW) is True
    assert scoring.is_stale(NOW - timedelta(days=10), NOW) is False


def test_combined_score_blends_and_caps():
    assert scoring.combined_score(0.95, 1.0, 0) == 0.95
    assert scoring.combined_score(0.95, 0.0, 0) == round(0.95 * 0.6, 3)  # stale drags it down
    assert scoring.combined_score(1.0, 1.0, 50) == 1.0  # bonus capped at 1.0
