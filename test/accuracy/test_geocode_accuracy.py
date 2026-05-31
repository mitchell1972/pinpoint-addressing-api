"""The north-star test (spec §11): forward-geocode top-candidate accuracy.

Runs free-text queries (no admin-area hint, the hard real-world case) against the
Lagos ground truth and asserts >=90% of top candidates are correct.

NON-GATING (xfail, strict=False) on purpose: a north-star you track, not a gate
that blocks merges. Note the pg_trgm baseline currently scores 100% here — that is
NOT a validated engine, it is an inadequate fixture set: 8 sparse addresses where
every query has exactly one trigram match. Before this number means anything, grow
test/fixtures with same-street collisions, misspellings, and genuinely ambiguous
pidgin where the correct answer is not the only candidate. Run: pytest -m accuracy -rX
"""

import pytest


@pytest.mark.accuracy
@pytest.mark.xfail(
    reason="Non-gating north-star (spec §11, >90%). Current 8-point fixture set is too "
    "small/sparse to be adversarial; the pg_trgm baseline clears it trivially and "
    "that does not validate the engine. Expand fixtures before trusting this.",
    strict=False,
)
async def test_forward_geocode_top_candidate_accuracy(client, test_auth, fixtures):
    correct = 0
    for f in fixtures:
        r = await client.post(
            "/v1/geocode",
            headers=test_auth,
            json={"query": f["query"], "limit": 1},  # no area hint on purpose
        )
        assert r.status_code == 200
        results = r.json()["results"]
        if results and results[0]["code"] == f["code"]:
            correct += 1

    rate = correct / len(fixtures)
    assert rate >= 0.90, (
        f"top-candidate accuracy {rate:.0%} < 90% target ({correct}/{len(fixtures)})"
    )
