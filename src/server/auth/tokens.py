"""Token verification: JWT first, then legacy static tokens."""
from .impl import verify_static_token, verify_token

__all__ = ["verify_static_token", "verify_token"]
