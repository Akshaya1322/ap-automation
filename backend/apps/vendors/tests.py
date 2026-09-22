from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import Role
from apps.common.test_utils import make_user, make_vendor
from apps.vendors.models import Vendor, VendorStatus


class VendorManagementTests(APITestCase):
    def setUp(self):
        self.manager = make_user(Role.AP_MANAGER, username="vmgr1")
        self.processor = make_user(Role.AP_PROCESSOR, username="vproc1")

    def test_create_requires_manager_role(self):
        self.client.force_authenticate(self.processor)
        response = self.client.post(reverse("vendor-list"), {"name": "Acme", "code": "VEN-X1"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_vendor_starts_as_draft_and_inactive(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(
            reverse("vendor-list"),
            {
                "name": "Acme Supplies",
                "code": "VEN-X2",
                "bank_details": {
                    "account_holder_name": "Acme Supplies",
                    "account_number": "111122223333",
                    "bank_name": "Test Bank",
                    "ifsc_code": "TEST0009999",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], VendorStatus.DRAFT)
        vendor = Vendor.objects.get(id=response.data["id"])
        self.assertFalse(vendor.is_active)
        # bank details must never be exposed unmasked
        self.assertNotIn("1111", response.data["bank_details"]["masked_account_number"])
        self.assertTrue(response.data["bank_details"]["masked_account_number"].startswith("*"))

    def test_onboarding_transitions_must_happen_in_order(self):
        vendor = make_vendor(name="Order Test", with_bank=False)
        vendor.status = VendorStatus.DRAFT
        vendor.is_active = False
        vendor.save()

        self.client.force_authenticate(self.manager)
        # cannot approve before submit/review
        response = self.client.post(reverse("vendor-approve", args=[vendor.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(reverse("vendor-submit", args=[vendor.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], VendorStatus.SUBMITTED)

        response = self.client.post(reverse("vendor-start-review", args=[vendor.id]))
        self.assertEqual(response.data["status"], VendorStatus.UNDER_REVIEW)

        response = self.client.post(reverse("vendor-approve", args=[vendor.id]))
        self.assertEqual(response.data["status"], VendorStatus.APPROVED)

        response = self.client.post(reverse("vendor-activate", args=[vendor.id]))
        self.assertEqual(response.data["status"], VendorStatus.ACTIVE)
        vendor.refresh_from_db()
        self.assertTrue(vendor.is_active)

    def test_deactivate_active_vendor(self):
        vendor = make_vendor(name="Deactivate Me")
        self.client.force_authenticate(self.manager)
        response = self.client.post(reverse("vendor-deactivate", args=[vendor.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], VendorStatus.INACTIVE)
