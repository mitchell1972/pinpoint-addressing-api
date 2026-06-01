"""The north-star test (spec §11): forward-geocode top-candidate accuracy.

Runs free-text queries (no admin-area hint, the hard real-world case) against the
Lagos ground truth and asserts >=90% of top candidates are correct.

NON-GATING (xfail, strict=False) on purpose: a north-star you track, not a gate
that blocks merges. The fixture set now includes genuinely hard cases — same-area
collisions (two wharf gates, two Lekki gates), abbreviations (VI, unilag, bstop),
pidgin/filler words and a misspelling — so the score reflects real difficulty, not
a trivially-separable toy set. Run with the number visible: pytest test/accuracy -s
"""

import pytest


@pytest.mark.accuracy
@pytest.mark.xfail(
    reason="Non-gating north-star (spec §11, target >90%). The matcher is a pg_trgm + "
    "query-normalisation baseline and does not yet clear 90% on the hard fixture set; "
    "the engine work to close the gap is ongoing.",
    strict=False,
)
async def test_forward_geocode_top_candidate_accuracy(client, test_auth, fixtures):
    correct = 0
    misses = []
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
        else:
            got = results[0]["code"] if results else None
            misses.append(f"{f['query']!r} -> got {got}, expected {f['code']}")

    rate = correct / len(fixtures)
    print(
        f"\n[accuracy] forward-geocode top candidate correct: {correct}/{len(fixtures)} = {rate:.0%}"
    )
    for m in misses:
        print(f"   miss: {m}")
    assert rate >= 0.90, (
        f"top-candidate accuracy {rate:.0%} < 90% target ({correct}/{len(fixtures)})"
    )
