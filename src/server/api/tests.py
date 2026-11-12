from unittest.mock import patch

from django.test import SimpleTestCase

from server.auth.impl import issue_jwt, verify_jwt


class JWTAccountIdentityTests(SimpleTestCase):
    def test_jwt_round_trip_preserves_stable_account_id(self):
        with patch("server.auth.impl.config.JWT_SECRET", "test-jwt-secret"):
            token = issue_jwt(
                "duplicate-name",
                "Duplicate Name",
                account_user_id=42,
            )
            user = verify_jwt(token)

        self.assertIsNotNone(user)
        self.assertEqual(user.id, "duplicate-name")
        self.assertEqual(user.account_user_id, 42)

    def test_legacy_jwt_remains_valid_without_account_id(self):
        with patch("server.auth.impl.config.JWT_SECRET", "test-jwt-secret"):
            token = issue_jwt("legacy-user", "Legacy User")
            user = verify_jwt(token)

        self.assertIsNotNone(user)
        self.assertIsNone(user.account_user_id)
