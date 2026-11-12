import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from server.apps.accounts.models import User, Cohort, Batch, Lab, SubBatch


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="Gaurav Rai",
            email="gaurav.rai@tcs.com",
            password="SecurePassword@123",
            first_name="Gaurav",
            last_name="Rai",
            role="ADMIN",
            employee_id="3273115",
            is_staff=True,
        )
        self.trainee = User.objects.create_user(
            username="Trainee One",
            email="trainee1@tcs.com",
            password="SecurePassword@123",
            role="TRAINEE",
            is_staff=False,
        )

    def test_admin_login_success(self):
        response = self.client.post(
            "/api/accounts/login/",
            {"email": "gaurav.rai@tcs.com", "password": "SecurePassword@123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["email"], "gaurav.rai@tcs.com")
        self.assertEqual(response.data["full_name"], "Gaurav Rai")
        self.assertEqual(response.data["role"], "ADMIN")

    def test_trainee_login_blocked_from_admin_console(self):
        response = self.client.post(
            "/api/accounts/login/",
            {"email": "trainee1@tcs.com", "password": "SecurePassword@123"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.data)

    def test_invalid_credentials_returns_401(self):
        response = self.client.post(
            "/api/accounts/login/",
            {"email": "gaurav.rai@tcs.com", "password": "WrongPassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


class UserProfileAndSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="Gaurav Rai",
            email="gaurav.rai@tcs.com",
            password="Password@123",
            first_name="Gaurav",
            last_name="Rai",
            role="ADMIN",
            employee_id="3273115",
            department="TCS Ignite",
            designation="Ignite Administrator",
            is_staff=True,
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_own_profile(self):
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["full_name"], "Gaurav Rai")
        self.assertEqual(response.data["email"], "gaurav.rai@tcs.com")
        self.assertEqual(response.data["employee_id"], "3273115")

    def test_patch_own_profile(self):
        response = self.client.patch(
            "/api/accounts/me/",
            {"department": "TCS Ignite Innovations", "designation": "Lead Architect"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("phone_number", response.data)
        self.assertEqual(response.data["department"], "TCS Ignite Innovations")
        self.assertEqual(response.data["designation"], "Lead Architect")

        self.user.refresh_from_db()
        self.assertEqual(self.user.department, "TCS Ignite Innovations")
        self.assertEqual(self.user.designation, "Lead Architect")

    def test_protected_fields_cannot_be_escalated(self):
        response = self.client.patch(
            "/api/accounts/me/",
            {"role": "SUPER_ADMIN", "employee_id": "HACKED"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "ADMIN")
        self.assertEqual(self.user.employee_id, "3273115")

    def test_change_password_success(self):
        response = self.client.post(
            "/api/accounts/change-password/",
            {"old_password": "Password@123", "new_password": "NewSecurePassword@456"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify old password no longer works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePassword@456"))
        self.assertFalse(self.user.check_password("Password@123"))

    def test_change_password_wrong_old_password(self):
        response = self.client.post(
            "/api/accounts/change-password/",
            {"old_password": "WrongOldPassword", "new_password": "NewSecurePassword@456"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class RolesPermissionsAndSettingsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="Admin",
            email="admin@tcs.com",
            password="AdminPassword@123",
            role="ADMIN",
            is_staff=True,
            is_superuser=True,
        )
        self.token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_roles_permissions_matrix(self):
        response = self.client.get("/api/accounts/roles-permissions/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("roles", response.data)
        self.assertIn("ADMIN", response.data["roles"])
        self.assertIn("TRAINEE", response.data["roles"])
        self.assertTrue(response.data["can_manage"])

    def test_update_roles_permissions(self):
        roles = {
            "TA": {
                "label": "Faculty / Teaching Assistant",
                "permissions": {"dashboard": True, "schedule": True, "buddy": False},
            }
        }
        response = self.client.post(
            "/api/accounts/roles-permissions/",
            {"roles": roles},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    def test_get_and_post_system_preferences(self):
        get_res = self.client.get("/api/settings/preferences/")
        self.assertEqual(get_res.status_code, 200)
        self.assertIn("workspace_name", get_res.data)

        # Update preferences
        post_res = self.client.post(
            "/api/settings/preferences/",
            {"workspace_name": "Ignite Buddy Workspace", "theme": "dark"},
            format="json",
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertEqual(post_res.data["preferences"]["workspace_name"], "Ignite Buddy Workspace")
        self.assertEqual(post_res.data["preferences"]["theme"], "dark")

    def test_export_users_csv(self):
        response = self.client.get("/api/settings/export/?type=users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("Employee ID", content)
        self.assertIn("admin@tcs.com", content)

    def test_export_audit_json(self):
        response = self.client.get("/api/settings/export/?type=audit")
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_users", response.data)
        self.assertIn("exported_at", response.data)


class HierarchyAndUserManagementTests(TestCase):
    def setUp(self):
        self.cohort = Cohort.objects.create(name="Ignite Cohort 2026", code="C26")
        self.batch = Batch.objects.create(name="Batch 1", cohort=self.cohort)
        self.lab = Lab.objects.create(name="Lab Delta")
        self.sub_batch = SubBatch.objects.create(name="Delta 1", batch=self.batch, lab=self.lab)

    def test_hierarchy_relationship(self):
        self.assertEqual(self.batch.cohort.name, "Ignite Cohort 2026")
        self.assertEqual(self.sub_batch.batch.name, "Batch 1")
        self.assertEqual(self.sub_batch.lab.name, "Lab Delta")

    def test_user_batch_naming(self):
        user = User.objects.create_user(
            username="Student",
            email="student@tcs.com",
            password="Password@123",
            role="TRAINEE",
            sub_batch=self.sub_batch,
        )
        self.assertIn("C26", user.full_batch_name)
        self.assertIn("Delta 1", user.full_batch_name)
