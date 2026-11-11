"""Trainee authentication: passwords, JWT, legacy static tokens.

Used by the WebSocket handshake and by POST /auth/login.
"""
from .passwords import hash_password, verify_password
from .jwt_tokens import issue_jwt, verify_jwt
from .tokens import verify_static_token, verify_token

__all__ = [
    "hash_password", "verify_password",
    "issue_jwt", "verify_jwt",
    "verify_static_token", "verify_token",
]
