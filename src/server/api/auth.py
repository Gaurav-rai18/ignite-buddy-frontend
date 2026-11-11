"""Admin token authentication (X-Admin-Token header)."""
import hmac

from rest_framework import authentication, exceptions

from server import config


class AdminTokenAuthentication(authentication.BaseAuthentication):
    """Authenticate requests that carry a valid X-Admin-Token.

    When ASSISTANT_ADMIN_TOKEN is empty the API is disabled (every request
    is rejected). Uses constant-time comparison.
    """

    header = "X-Admin-Token"

    def authenticate(self, request):
        given = request.headers.get(self.header, "")
        if not given:
            return None
        expected = config.ADMIN_TOKEN or ""
        if not expected:
            raise exceptions.AuthenticationFailed("admin API disabled (ASSISTANT_ADMIN_TOKEN is empty)")
        if not hmac.compare_digest(given, expected):
            raise exceptions.AuthenticationFailed("invalid admin token")
        # No user object; admin is a single shared capability.
        return (None, given)

    def authenticate_header(self, request):
        # Return None so DRF responds with 403 (not 401) when the token is missing/invalid.
        # The admin panel is a shared-token capability, not a challengeable WWW-Authenticate flow.
        return None
