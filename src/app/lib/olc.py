"""Plus Code (Open Location Code) wrapper.

We deliberately do not invent a grid code (spec §2.3, §9.2) — we wrap Google's
reference implementation and interoperate. The human-shareable `PIN-XXXX-XX`
alias lives in lib/codes.py.
"""

from openlocationcode import openlocationcode as _olc

# 11 chars ≈ ~3.5m resolution — enough to distinguish adjacent frontages.
DEFAULT_LENGTH = 11


def encode(lat: float, lng: float, length: int = DEFAULT_LENGTH) -> str:
    return _olc.encode(lat, lng, length)


def decode(code: str):
    """Return the CodeArea (centre + bounds) for a full Plus Code."""
    return _olc.decode(code)


def is_valid(code: str) -> bool:
    return _olc.isValid(code)
