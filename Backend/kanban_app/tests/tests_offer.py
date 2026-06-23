from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from kanban_app.models import Offer, OfferDetail


class OfferApiTests(APITestCase):
    """Integration tests for the offer endpoints under /api/offers/."""

    def setUp(self):
        self.business_user = User.objects.create_user(
            username="business_user",
            email="business@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.business_user, type="business")

        self.customer_user = User.objects.create_user(
            username="customer_user",
            email="customer@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.customer_user, type="customer")

        self.business_token = Token.objects.create(user=self.business_user)
        self.customer_token = Token.objects.create(user=self.customer_user)

        self.list_url = reverse("offer-list")

    def _details_payload(self):
        return [
            {
                "title": "Basic Design",
                "revisions": 1,
                "delivery_time_in_days": 5,
                "price": "100.00",
                "features": ["Logo Design", "Visitenkarte"],
                "offer_type": "basic",
            },
            {
                "title": "Standard Design",
                "revisions": 2,
                "delivery_time_in_days": 7,
                "price": "200.00",
                "features": ["Logo Design", "Visitenkarte", "Briefpapier"],
                "offer_type": "standard",
            },
            {
                "title": "Premium Design",
                "revisions": 3,
                "delivery_time_in_days": 10,
                "price": "500.00",
                "features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
                "offer_type": "premium",
            },
        ]

    def _create_offer_with_details(self, user, title, base_price):
        offer = Offer.objects.create(
            user=user,
            title=title,
            description=f"{title} description",
        )
        OfferDetail.objects.create(
            offer=offer,
            title=f"{title} Basic",
            revisions=2,
            delivery_time_in_days=5,
            price=base_price,
            features=["A"],
            offer_type="basic",
        )
        OfferDetail.objects.create(
            offer=offer,
            title=f"{title} Standard",
            revisions=2,
            delivery_time_in_days=5,
            price=base_price + 100,
            features=["A", "B"],
            offer_type="standard",
        )
        OfferDetail.objects.create(
            offer=offer,
            title=f"{title} Premium",
            revisions=3,
            delivery_time_in_days=7,
            price=base_price + 200,
            features=["A", "B", "C"],
            offer_type="premium",
        )
        return offer

    def test_offer_list_is_public(self):
        """GET /api/offers/ Test that the offer list endpoint is accessible without authentication."""
        self._create_offer_with_details(self.business_user, "Offer A", 100)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_offer_detail_requires_authentication(self):
        """GET/api/offers/{id}/ Test that the offer detail endpoint requires authentication."""
        offer = self._create_offer_with_details(self.business_user, "Offer A", 100)
        detail_url = reverse("offer-detail-detail", kwargs={"pk": offer.id})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_offer_detail_authentication(self):
        """GET/api/offers/{id}/ Test that the offer detail endpoint authenticates the user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        offer = self._create_offer_with_details(self.business_user, "Offer A", 100)
        detail_url = reverse("offer-detail", kwargs={"pk": offer.id})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_cannot_create_offer(self):
        """POST /api/offers/ 403 Test that a customer user cannot create an offer."""
        payload = {
            "title": "Customer Offer",
            "description": "Should fail",
            "details": self._details_payload(),
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_business_can_create_offer_with_three_details(self):
        """POST /api/offers/ 201 Test that a business user can create an offer with exactly three details."""
        payload = {
            "title": "Business Offer",
            "description": "Valid offer",
            "details": self._details_payload(),
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        offer = Offer.objects.get(title="Business Offer")
        self.assertEqual(offer.details.count(), 3)

    def test_create_offer_requires_exactly_three_details(self):
        """POST /api/offers/ 400 Test that creating an offer requires exactly three details."""
        payload = {
            "title": "Invalid Offer",
            "description": "Invalid detail count",
            "details": self._details_payload()[:2],
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("details", response.data)

    def test_offer_list_can_filter_by_creator_id(self):
        """GET /api/offers/?creator_id=... 200 Test that the offer list can be filtered by creator ID."""
        other_business = User.objects.create_user(
            username="other_business",
            email="other-business@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=other_business, type="business")

        offer_a = self._create_offer_with_details(self.business_user, "Offer A", 100)
        self._create_offer_with_details(other_business, "Offer B", 150)

        response = self.client.get(self.list_url, {"creator_id": self.business_user.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], offer_a.id)
