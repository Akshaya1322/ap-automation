from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import Role
from apps.common.test_utils import make_user


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = make_user(Role.AP_MANAGER, username="mgr1")

    def test_login_success_returns_tokens_and_role_claim(self):
        response = self.client.post(reverse("auth-login"), {"username": "mgr1", "password": "Test@12345"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], Role.AP_MANAGER)

    def test_login_invalid_credentials_rejected(self):
        response = self.client.post(reverse("auth-login"), {"username": "mgr1", "password": "wrong"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("auth-profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_current_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("auth-profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "mgr1")

    def test_change_password_requires_correct_old_password(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("auth-change-password"), {"old_password": "wrong", "new_password": "NewPass@123"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("auth-change-password"), {"old_password": "Test@12345", "new_password": "NewPass@123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass@123"))
