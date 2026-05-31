import hashlib
from dataclasses import dataclass


@dataclass
class Principal:
    """The authenticated caller, attached to request.state for metering."""

    account_id: str
    account_type: str
    api_key_id: str
    env: str  # 'test' | 'live'
    rate_limit: int


def hash_key(raw: str) -> str:
    """API keys are stored hashed, never in plaintext."""
    return hashlib.sha256(raw.encode()).hexdigest()
