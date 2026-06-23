from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from kanban_app.models import Offer, OfferDetail

"""It contains 5 passing tests for PATCH /api/offers/{id}/:

200 owner can update title and one nested detail
200 owner can update only the title and keep details unchanged
401 unauthenticated user cannot patch
403 authenticated non-owner cannot patch
404 patching a missing offer returns not found"""


class OfferPatchApiTests(TestCase):
    """Tests for PATCH /api/offers/{id}/."""

    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="offer_owner",
            email="owner@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.owner, type="business")
        self.owner_token = Token.objects.create(user=self.owner)

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.other_user, type="business")
        self.other_token = Token.objects.create(user=self.other_user)

        self.offer = self._create_offer_with_details(
            user=self.owner,
            title="Original Grafikdesign-Paket",
            description="Ein umfassendes Grafikdesign-Paket fuer Unternehmen.",
        )
        self.url = f"/api/offers/{self.offer.id}/"

    def _create_offer_with_details(self, user, title, description):
        offer = Offer.objects.create(
            user=user,
            title=title,
            description=description,
        )
        OfferDetail.objects.create(
            offer=offer,
            title="Basic Design",
            revisions=2,
            delivery_time_in_days=5,
            price="100.00",
            features=["Logo Design", "Visitenkarte"],
            offer_type="basic",
        )
        OfferDetail.objects.create(
            offer=offer,
            title="Standard Design",
            revisions=5,
            delivery_time_in_days=10,
            price="120.00",
            features=["Logo Design", "Visitenkarte", "Briefpapier"],
            offer_type="standard",
        )
        OfferDetail.objects.create(
            offer=offer,
            title="Premium Design",
            revisions=10,
            delivery_time_in_days=10,
            price="150.00",
            features=["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
            offer_type="premium",
        )
        return offer

    def test_owner_can_patch_offer_title_and_one_detail(self):
        """The owner can update the title and one nested detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.owner_token.key}")
        payload = {
            "title": "Updated Grafikdesign-Paket",
            "details": [
                {
                    "title": "Basic Design Updated",
                    "revisions": 3,
                    "delivery_time_in_days": 6,
                    "price": "120.00",
                    "features": ["Logo Design", "Flyer"],
                    "offer_type": "basic",
                }
            ],
        }

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Grafikdesign-Paket")
        self.assertEqual(response.data["description"], self.offer.description)
        self.assertEqual(len(response.data["details"]), 3)

        self.offer.refresh_from_db()
        basic_detail = self.offer.details.get(offer_type="basic")
        standard_detail = self.offer.details.get(offer_type="standard")
        premium_detail = self.offer.details.get(offer_type="premium")

        self.assertEqual(self.offer.title, "Updated Grafikdesign-Paket")
        self.assertEqual(basic_detail.title, "Basic Design Updated")
        self.assertEqual(basic_detail.revisions, 3)
        self.assertEqual(basic_detail.delivery_time_in_days, 6)
        self.assertEqual(str(basic_detail.price), "120.00")
        self.assertEqual(basic_detail.features, ["Logo Design", "Flyer"])
        self.assertEqual(standard_detail.title, "Standard Design")
        self.assertEqual(premium_detail.title, "Premium Design")

    def test_owner_can_patch_only_title_and_leave_details_unchanged(self):
        """A partial PATCH updates only provided top-level fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.owner_token.key}")

        response = self.client.patch(
            self.url,
            {"title": "Title Only Update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "Title Only Update")
        self.assertEqual(
            self.offer.details.get(offer_type="basic").title,
            "Basic Design",
        )

    def test_unauthenticated_user_cannot_patch_offer(self):
        """An unauthenticated request returns 401."""
        response = self.client.patch(
            self.url,
            {"title": "Unauthorized Update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_non_owner_cannot_patch_offer(self):
        """A different authenticated user receives 403."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")

        response = self.client.patch(
            self.url,
            {"title": "Forbidden Update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_nonexistent_offer_returns_404(self):
        """Patching an unknown offer id returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.owner_token.key}")

        response = self.client.patch(
            "/api/offers/999999/",
            {"title": "Missing Offer"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
