from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from kanban_app.models import Offer, OfferDetail

"""It contains 8 passing tests for GET /api/offers/, covering:

creator_id
min_price
max_delivery_time
ordering by min_price
ordering by -min_price
ordering by -updated_at
search
page_size"""


class OfferFilterAndOrderingTests(TestCase):
    """Tests for filtering, searching, pagination, and ordering on GET /api/offers/."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/offers/"

        self.business_user = User.objects.create_user(
            username="business_one",
            email="business-one@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.business_user, type="business")

        self.other_business_user = User.objects.create_user(
            username="business_two",
            email="business-two@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.other_business_user, type="business")

        self.offer_alpha = self._create_offer(
            user=self.business_user,
            title="Alpha Branding",
            description="Professional logo and branding package",
            basic_price=90,
            basic_days=3,
        )
        self.offer_beta = self._create_offer(
            user=self.business_user,
            title="Beta Website",
            description="Modern web design for startups",
            basic_price=140,
            basic_days=5,
        )
        self.offer_gamma = self._create_offer(
            user=self.other_business_user,
            title="Gamma Marketing",
            description="SEO content and campaign support",
            basic_price=220,
            basic_days=9,
        )

        Offer.objects.filter(pk=self.offer_alpha.pk).update(
            updated_at=timezone.now() - timedelta(days=2)
        )
        Offer.objects.filter(pk=self.offer_beta.pk).update(
            updated_at=timezone.now() - timedelta(days=1)
        )
        Offer.objects.filter(pk=self.offer_gamma.pk).update(updated_at=timezone.now())

        self.offer_alpha.refresh_from_db()
        self.offer_beta.refresh_from_db()
        self.offer_gamma.refresh_from_db()

    def _create_offer(self, user, title, description, basic_price, basic_days):
        offer = Offer.objects.create(
            user=user,
            title=title,
            description=description,
        )
        OfferDetail.objects.create(
            offer=offer,
            title=f"{title} Basic",
            revisions=1,
            delivery_time_in_days=basic_days,
            price=basic_price,
            features=["Feature A"],
            offer_type="basic",
        )
        OfferDetail.objects.create(
            offer=offer,
            title=f"{title} Standard",
            revisions=2,
            delivery_time_in_days=basic_days + 2,
            price=basic_price + 80,
            features=["Feature A", "Feature B"],
            offer_type="standard",
        )
        OfferDetail.objects.create(
            offer=offer,
            title=f"{title} Premium",
            revisions=3,
            delivery_time_in_days=basic_days + 4,
            price=basic_price + 160,
            features=["Feature A", "Feature B", "Feature C"],
            offer_type="premium",
        )
        return offer

    def test_filters_offers_by_creator_id(self):
        response = self.client.get(self.url, {"creator_id": self.business_user.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.offer_alpha.id, self.offer_beta.id],
        )

    def test_filters_offers_by_min_price_query(self):
        response = self.client.get(self.url, {"min_price": 135})

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.offer_beta.id, self.offer_gamma.id],
        )

    def test_filters_offers_by_max_delivery_time(self):
        response = self.client.get(self.url, {"max_delivery_time": 4})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]], [self.offer_alpha.id]
        )

    def test_orders_offers_by_min_price_ascending(self):
        response = self.client.get(self.url, {"ordering": "min_price"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.offer_alpha.id, self.offer_beta.id, self.offer_gamma.id],
        )

    def test_orders_offers_by_min_price_and_max_delivery_timeascending(self):
        response = self.client.get(
            self.url,
            {"min_price": 135, "max_delivery_time": 7, "ordering": "min_price"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.offer_beta.id],
        )

    def test_orders_offers_by_min_price_descending(self):
        response = self.client.get(self.url, {"ordering": "-min_price"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.offer_gamma.id, self.offer_beta.id, self.offer_alpha.id],
        )

    def test_orders_offers_by_updated_at_descending(self):
        response = self.client.get(self.url, {"ordering": "-updated_at"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.offer_gamma.id, self.offer_beta.id, self.offer_alpha.id],
        )

    def test_searches_offers_by_title_and_description(self):
        response = self.client.get(self.url, {"search": "startups"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["results"]], [self.offer_beta.id]
        )

    def test_supports_page_size_pagination_when_requested(self):
        response = self.client.get(self.url, {"page_size": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
