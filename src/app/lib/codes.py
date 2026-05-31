"""Human-shareable address alias, e.g. PIN-7F3K-QM (spec §9.2).

Crockford base-32 alphabet (no I/L/O/U) to avoid ambiguity when read aloud over
a phone — the dominant way Nigerian couriers confirm locations today. Uniqueness
is enforced by the DB unique constraint; the addresses repo retries on collision.
"""
import secrets

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_alias() -> str:
    s = "".join(secrets.choice(_CROCKFORD) for _ in range(6))
    return f"PIN-{s[:4]}-{s[4:]}"
