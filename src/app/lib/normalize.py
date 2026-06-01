"""Tidy a free-text search query before matching.

Lowercases, strips punctuation, expands common address/Nigerian short-forms,
turns number-words into digits ("second" -> "2", so it lines up with "Gate 2"),
and drops filler/pidgin words. The goal is to make the query read the way places
are actually written down, giving the matcher its best chance.

Applied to the query only: the matcher (pg_trgm) already lowercases and ignores
punctuation on the stored side, so case/punctuation/typos are handled there.
"""

import re

# Short-forms -> full words. A value may contain a space (e.g. "bus stop");
# it is split back into separate words after lookup.
_EXPANSIONS = {
    "rd": "road",
    "st": "street",
    "str": "street",
    "ave": "avenue",
    "av": "avenue",
    "cresc": "crescent",
    "expy": "expressway",
    "hwy": "highway",
    "jcn": "junction",
    "jct": "junction",
    "junc": "junction",
    "rdabt": "roundabout",
    "rndabt": "roundabout",
    "opp": "opposite",
    "stn": "station",
    "bstop": "bus stop",
    "busstop": "bus stop",
    "vi": "victoria island",
    "unilag": "university of lagos",
    "1st": "1",
    "2nd": "2",
    "3rd": "3",
    "4th": "4",
    "5th": "5",
    "first": "1",
    "second": "2",
    "third": "3",
    "fourth": "4",
    "fifth": "5",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
}

# Filler / pidgin words that carry no location meaning. Locational words
# (under, opposite, beside, behind, near, back) are deliberately kept.
_STOPWORDS = {
    "for",
    "wey",
    "dey",
    "na",
    "abeg",
    "go",
    "the",
    "of",
    "at",
    "by",
    "to",
    "and",
    "a",
    "an",
    "is",
    "my",
    "where",
}


def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    tokens: list[str] = []
    for raw in s.split():
        tokens.extend(_EXPANSIONS.get(raw, raw).split())
    kept = [t for t in tokens if t not in _STOPWORDS]
    # Never return empty (e.g. an all-filler query) — fall back to the cleaned tokens.
    return " ".join(kept) if kept else " ".join(tokens)
