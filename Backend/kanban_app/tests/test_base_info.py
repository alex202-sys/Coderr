from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from kanban_app.models import Offer, Review

""" It covers GET /api/base-info/ from the PDF with 4 passing tests:
- public access
- xpected response keys
- correct aggregated values
- zero values when no data exists
run: 
cd "C:/Users/aleks/Desktop/DJANGO_PROJECT/Coderr/Backend"
.\venv\Scripts\activate
python manage.py test kanban_app.tests.test_base_info """


class BaseInfoApiTests(TestCase):
    """Tests for GET /api/base-info/."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/base-info/"

        self.business_user_1 = User.objects.create_user(
            username="business_one",
            email="business-one@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.business_user_1, type="business")

        self.business_user_2 = User.objects.create_user(
            username="business_two",
            email="business-two@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.business_user_2, type="business")

        self.customer_user_1 = User.objects.create_user(
            username="customer_one",
            email="customer-one@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.customer_user_1, type="customer")

        self.customer_user_2 = User.objects.create_user(
            username="customer_two",
            email="customer-two@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.customer_user_2, type="customer")

        Offer.objects.create(
            user=self.business_user_1,
            title="Offer One",
            description="First offer",
        )
        Offer.objects.create(
            user=self.business_user_2,
            title="Offer Two",
            description="Second offer",
        )

        Review.objects.create(
            business_user=self.business_user_1,
            reviewer=self.customer_user_1,
            rating=4,
            description="Very good",
        )
        Review.objects.create(
            business_user=self.business_user_2,
            reviewer=self.customer_user_2,
            rating=5,
            description="Excellent",
        )

    def test_base_info_is_public(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_base_info_returns_expected_keys(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data.keys()),
            {"review_count", "average_rating", "business_profile_count", "offer_count"},
        )

    def test_base_info_returns_correct_aggregated_values(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["review_count"], 2)
        self.assertEqual(response.data["average_rating"], 4.5)
        self.assertEqual(response.data["business_profile_count"], 2)
        self.assertEqual(response.data["offer_count"], 2)

    def test_base_info_returns_zero_values_when_no_data_exists(self):
        Review.objects.all().delete()
        Offer.objects.all().delete()
        UserProfile.objects.filter(type="business").delete()
        User.objects.filter(username__in=["business_one", "business_two"]).delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["review_count"], 0)
        self.assertEqual(response.data["average_rating"], 0)
        self.assertEqual(response.data["business_profile_count"], 0)
        self.assertEqual(response.data["offer_count"], 0)
