"""Password hashing and session tokens for Campus Customs.

Passwords are never stored, logged, or returned by the API. What lands in the
`users.password_hash` column is a PBKDF2-HMAC-SHA256 digest with a per-user
random salt — a one-way function, so the stored value cannot be reversed into
the password even by someone holding the database file.

Two hash formats are supported:

    pbkdf2_sha256$<salt>$<hex>               legacy — 120,000 iterations implied
    pbkdf2_sha256$<iterations>$<salt>$<hex>  current — iterations stored

The legacy three-part form is what the seeded test user ships with. Because that
format does not record its iteration count, the work factor could never be
raised without locking those users out. The four-part form fixes that: new
accounts record their own cost, and a legacy hash is transparently upgraded the
next time that user logs in successfully.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

# OWASP's recommended PBKDF2-HMAC-SHA256 work factor. Raising this later is now
# safe — the value travels inside each hash, so old passwords still verify.
ITERATIONS = 600_000

# The iteration count the seeded hashes were created with. Recovered by matching
# the known test password against the stored digest; it is not recorded anywhere
# in the three-part format itself.
LEGACY_ITERATIONS = 120_000

ALGORITHM = "pbkdf2_sha256"
SALT_BYTES = 16

# Signing key for session tokens. Generated per-install into backend/.env, which
# is gitignored — a hardcoded fallback would mean every clone of this repo could
# forge tokens for every other.
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # one week


def hash_password(password: str, *, iterations: int = ITERATIONS) -> str:
    """Hash a password with a fresh random salt.

    Salting per user means two people choosing the same password still get
    different digests, so a precomputed rainbow table is useless here.
    """
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return f"{ALGORITHM}${iterations}${salt}${digest}"


def _parse(stored: str) -> tuple[int, str, str] | None:
    """Pull (iterations, salt, digest) out of either supported hash format."""
    parts = stored.split("$")
    if len(parts) == 3 and parts[0] == ALGORITHM:
        # Legacy: iterations were a constant in the seed script, not stored.
        return LEGACY_ITERATIONS, parts[1], parts[2]
    if len(parts) == 4 and parts[0] == ALGORITHM:
        try:
            return int(parts[1]), parts[2], parts[3]
        except ValueError:
            return None
    return None


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash, in constant time."""
    parsed = _parse(stored)
    if parsed is None:
        return False
    iterations, salt, expected = parsed
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    # compare_digest, not ==, so the time taken does not leak how many leading
    # characters of the digest matched.
    return hmac.compare_digest(candidate, expected)


def needs_rehash(stored: str) -> bool:
    """True when a hash was made with weaker parameters than we now use."""
    parsed = _parse(stored)
    if parsed is None:
        return False
    return parsed[0] < ITERATIONS


# --- Session tokens ----------------------------------------------------------
#
# Format: <user_id>.<expires_at>.<hmac signature>
#
# Signed rather than random-and-stored, so sessions survive a backend restart
# without a session table. The signature is what makes the token unforgeable —
# a user cannot edit the id in their own token to become someone else.


def _sign(payload: str) -> str:
    return hmac.new(
        SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def create_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_TTL_SECONDS}"
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str) -> int | None:
    """Return the user id if the token is authentic and unexpired, else None."""
    try:
        user_id_raw, expires_raw, signature = token.rsplit(".", 2)
    except ValueError:
        return None

    payload = f"{user_id_raw}.{expires_raw}"
    if not hmac.compare_digest(_sign(payload), signature):
        return None

    try:
        if int(expires_raw) < time.time():
            return None
        return int(user_id_raw)
    except ValueError:
        return None
