from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from kanban_app.models import Offer, OfferDetail


class OfferDeleteApiTests(TestCase):
    """Tests for DELETE /api/offers/{id}/."""

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
            title="Offer To Delete",
            description="Offer used for delete endpoint tests",
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
            revisions=1,
            delivery_time_in_days=3,
            price="100.00",
            features=["Logo"],
            offer_type="basic",
        )
        OfferDetail.objects.create(
            offer=offer,
            title="Standard Design",
            revisions=2,
            delivery_time_in_days=5,
            price="200.00",
            features=["Logo", "Brand Guide"],
            offer_type="standard",
        )
        OfferDetail.objects.create(
            offer=offer,
            title="Premium Design",
            revisions=3,
            delivery_time_in_days=7,
            price="300.00",
            features=["Logo", "Brand Guide", "Assets"],
            offer_type="premium",
        )
        return offer

    def test_owner_can_delete_own_offer(self):
        """The offer owner receives 204 and the offer is removed."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.owner_token.key}")

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Offer.objects.filter(pk=self.offer.id).exists())

    def test_unauthenticated_user_cannot_delete_offer(self):
        """An unauthenticated request returns 401."""
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Offer.objects.filter(pk=self.offer.id).exists())

    def test_authenticated_non_owner_cannot_delete_offer(self):
        """A different authenticated user receives 403."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(pk=self.offer.id).exists())

    def test_delete_nonexistent_offer_returns_404(self):
        """Deleting an unknown offer id returns 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.owner_token.key}")

        response = self.client.delete("/api/offers/999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
