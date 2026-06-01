from app.lib import ledger


def _fields(addr, score):
    return ledger.chain_fields(
        addr, "kyc", score, 1.0, {"device": "x"}, "system", "2026-06-01T00:00:00+00:00"
    )


def _entry(seq, prev, fields):
    return {**fields, "seq": seq, "prev_hash": prev, "entry_hash": ledger.entry_hash(prev, fields)}


def test_hash_is_deterministic():
    f = _fields("a1", 0.9)
    assert ledger.entry_hash(ledger.GENESIS, f) == ledger.entry_hash(ledger.GENESIS, f)


def test_valid_chain_passes():
    e1 = _entry(1, ledger.GENESIS, _fields("a1", 0.9))
    e2 = _entry(2, e1["entry_hash"], _fields("a2", 0.8))
    ok, broken = ledger.verify_chain([e1, e2])
    assert ok is True
    assert broken is None


def test_tampering_breaks_the_chain():
    e1 = _entry(1, ledger.GENESIS, _fields("a1", 0.9))
    e2 = _entry(2, e1["entry_hash"], _fields("a2", 0.8))
    e1["score"] = 0.01  # edit a past entry after the fact
    ok, broken = ledger.verify_chain([e1, e2])
    assert ok is False
    assert broken == 1
