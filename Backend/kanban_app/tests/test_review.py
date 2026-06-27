from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from kanban_app.models import Review

"""
It includes tests for all requested review endpoints:
GET /api/reviews/
POST /api/reviews/
PATCH /api/reviews/{id}/
DELETE /api/reviews/{id}/
run: python manage.py test kanban_app.tests.test_review --noinput
"""


class ReviewApiTests(TestCase):
    """Tests for review endpoints: GET/POST/PATCH/DELETE /api/reviews/."""

    def setUp(self):
        self.client = APIClient()

        self.customer_user = User.objects.create_user(
            username="customer_user",
            email="customer@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.customer_user, type="customer")
        self.customer_token = Token.objects.create(user=self.customer_user)

        self.business_user = User.objects.create_user(
            username="business_user",
            email="business@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.business_user, type="business")

        self.other_customer = User.objects.create_user(
            username="other_customer",
            email="other-customer@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.other_customer, type="customer")
        self.other_customer_token = Token.objects.create(user=self.other_customer)

        self.review = Review.objects.create(
            business_user=self.business_user,
            reviewer=self.customer_user,
            rating=4,
            description="Very good service.",
        )

        self.list_url = "/api/reviews/"
        self.detail_url = f"/api/reviews/{self.review.id}/"

    def test_get_reviews_requires_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_reviews_returns_list_for_authenticated_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.review.id)

    def test_post_review_as_customer_returns_201(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.other_customer_token.key}"
        )
        payload = {
            "business_user": self.business_user.id,
            "rating": 5,
            "description": "Excellent.",
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_user"], self.business_user.id)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["reviewer"], self.other_customer.id)

    def test_post_review_as_business_user_returns_403(self):
        business_token = Token.objects.create(user=self.business_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {business_token.key}")
        payload = {
            "business_user": self.business_user.id,
            "rating": 5,
            "description": "Should fail.",
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_duplicate_review_for_same_business_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")
        payload = {
            "business_user": self.business_user.id,
            "rating": 3,
            "description": "Duplicate review.",
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_review_by_owner_returns_200(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")
        payload = {
            "rating": 5,
            "description": "Updated review text.",
        }

        response = self.client.patch(self.detail_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.description, "Updated review text.")

    def test_patch_review_by_non_owner_returns_403(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.other_customer_token.key}"
        )

        response = self.client.patch(
            self.detail_url,
            {"rating": 2, "description": "Not allowed."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_nonexistent_review_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.patch(
            "/api/reviews/999999/",
            {"rating": 2, "description": "Missing."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_review_by_owner_returns_204(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(pk=self.review.id).exists())

    def test_delete_review_by_non_owner_returns_403(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.other_customer_token.key}"
        )

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_review_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.delete("/api/reviews/999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
