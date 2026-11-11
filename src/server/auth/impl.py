"""Authentication for trainee WebSocket connections and HTTP login.

DEV (legacy static tokens)
    ASSISTANT_TOKENS="tokA:alice,tokB:bob" or ASSISTANT_TOKEN (single user).
    With none configured, static-token login is refused (fail closed).

JWT (preferred for desktop login)
    Admin creates the trainee profile (user_id + password) via the Admin API.
    Desktop app POSTs /auth/login → receives a JWT → sends it as the WebSocket
    auth token. Signature: HS256 with ASSISTANT_JWT_SECRET.

PRODUCTION note
    You can still replace verify_token() with OIDC/JWKS validation against the
    organisation IdP; map claims → User(id, name, role) the same way.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any

from server import config
from server.domain.session import User

# ---------------------------------------------------------------------------
# Password hashing (stdlib only — no extra dependency)
# ---------------------------------------------------------------------------

_PBKDF2_ROUNDS = 120_000


def hash_password(password: str, salt: str | None = None) -> str:
    """Return ``salt$hexdigest`` suitable for storage in trainees.password_hash."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), stored)


# ---------------------------------------------------------------------------
# JWT (minimal HS256 — avoids requiring PyJWT if unavailable; uses stdlib)
# ---------------------------------------------------------------------------

def _b64url(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    import base64
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def issue_jwt(user_id: str, name: str, batch: str = "default") -> str:
    """Issue a signed JWT for a trainee. Requires config.JWT_SECRET."""
    import json
    if not config.JWT_SECRET:
        raise RuntimeError("ASSISTANT_JWT_SECRET is not set; cannot issue tokens")
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    now = int(time.time())
    payload = {
        "sub": user_id,
        "name": name,
        "batch": batch,
        "iat": now,
        "exp": now + int(config.JWT_TTL_HOURS) * 3600,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64url(hmac.new(config.JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def verify_jwt(token: str) -> User | None:
    """Validate HS256 JWT and return User, or None if invalid/expired."""
    import json
    if not config.JWT_SECRET or token.count(".") != 2:
        return None
    header_b64, body_b64, sig_b64 = token.split(".")
    expected = _b64url(hmac.new(config.JWT_SECRET.encode(), f"{header_b64}.{body_b64}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_b64):
        return None
    try:
        payload: dict[str, Any] = json.loads(_b64url_decode(body_b64))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    uid = payload.get("sub")
    if not uid:
        return None
    return User(
        id=str(uid),
        name=str(payload.get("name") or uid),
        batch=str(payload.get("batch") or "default"),
    )


# ---------------------------------------------------------------------------
# Legacy static tokens
# ---------------------------------------------------------------------------

def _table() -> list[tuple[str, str]]:
    pairs = []
    for item in config.TOKENS_ENV.split(","):
        if ":" in item:
            tok, name = item.split(":", 1)
            if tok.strip() and name.strip():
                pairs.append((tok.strip(), name.strip()))
    if config.SINGLE_TOKEN:
        pairs.append((config.SINGLE_TOKEN, "dev-user"))
    return pairs


def verify_static_token(token: str) -> User | None:
    if not isinstance(token, str) or not token:
        return None
    found = None
    for tok, name in _table():  # no early exit: constant-ish time
        if hmac.compare_digest(token, tok):
            found = name
    return User(id=found, name=found) if found else None


def verify_token(token: str) -> User | None:
    """Accept either a JWT or a legacy static token."""
    if not isinstance(token, str) or not token:
        return None
    user = verify_jwt(token)
    if user:
        return user
    return verify_static_token(token)
