from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from kanban_app.models import Offer, OfferDetail, Order

"""
   - GET /api/orders/
   - POST /api/orders/
   - PATCH /api/orders/{id}/
   - DELETE /api/orders/{id}/
   - GET /api/order-count/{business_user_id}/
   - GET /api/completed-order-count/{business_user_id}/
     run: cd Backend
        venv/scripts/activate 
        python manage.py test kanban_app.tests.test_orders --noinput
"""


class OrdersApiTests(TestCase):
    """Integration tests for the orders endpoints described in the PDF spec."""

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
        self.business_token = Token.objects.create(user=self.business_user)

        self.other_business_user = User.objects.create_user(
            username="other_business",
            email="other-business@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.other_business_user, type="business")
        self.other_business_token = Token.objects.create(user=self.other_business_user)

        self.other_customer_user = User.objects.create_user(
            username="other_customer",
            email="other-customer@example.com",
            password="Test1234!",
        )
        UserProfile.objects.create(user=self.other_customer_user, type="customer")

        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="Test1234!",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.offer = Offer.objects.create(
            user=self.business_user,
            title="Logo Package",
            description="Business design package",
        )
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            title="Logo Design",
            revisions=3,
            delivery_time_in_days=5,
            price="150.00",
            features=["Logo Design", "Visitenkarten"],
            offer_type="basic",
        )
        OfferDetail.objects.create(
            offer=self.offer,
            title="Standard Design",
            revisions=5,
            delivery_time_in_days=7,
            price="250.00",
            features=["Logo Design", "Brand Guide"],
            offer_type="standard",
        )
        OfferDetail.objects.create(
            offer=self.offer,
            title="Premium Design",
            revisions=10,
            delivery_time_in_days=10,
            price="350.00",
            features=["Logo Design", "Brand Guide", "Flyer"],
            offer_type="premium",
        )

        self.related_order = Order.objects.create(
            offer_detail=self.offer_detail,
            customer_user=self.customer_user,
            business_user=self.business_user,
            title=self.offer_detail.title,
            revisions=self.offer_detail.revisions,
            delivery_time_in_days=self.offer_detail.delivery_time_in_days,
            price=self.offer_detail.price,
            features=self.offer_detail.features,
            offer_type=self.offer_detail.offer_type,
            status="in_progress",
        )
        self.completed_order = Order.objects.create(
            offer_detail=self.offer_detail,
            customer_user=self.customer_user,
            business_user=self.business_user,
            title="Completed Logo Design",
            revisions=self.offer_detail.revisions,
            delivery_time_in_days=self.offer_detail.delivery_time_in_days,
            price=self.offer_detail.price,
            features=self.offer_detail.features,
            offer_type=self.offer_detail.offer_type,
            status="completed",
        )
        self.unrelated_order = Order.objects.create(
            offer_detail=self.offer_detail,
            customer_user=self.other_customer_user,
            business_user=self.other_business_user,
            title="Unrelated Order",
            revisions=self.offer_detail.revisions,
            delivery_time_in_days=self.offer_detail.delivery_time_in_days,
            price=self.offer_detail.price,
            features=self.offer_detail.features,
            offer_type=self.offer_detail.offer_type,
            status="in_progress",
        )

        self.orders_url = "/api/orders/"
        self.order_detail_url = f"/api/orders/{self.related_order.id}/"
        self.order_count_url = "/api/order-count/{}/"
        self.completed_order_count_url = "/api/completed-order-count/{}/"

    def test_orders_list_requires_authentication(self):
        """GET /api/orders/ unauthenticated users should receive
        a 401 Unauthorized response."""
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_orders_list_returns_only_orders_related_to_authenticated_customer(self):
        """GET /api/orders/ authenticated customer should only see orders where they
        are the customer."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.get(self.orders_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data},
            {self.related_order.id, self.completed_order.id},
        )

    def test_orders_list_returns_only_orders_related_to_authenticated_business(self):
        """GET /api/orders/ authenticated business should only see orders where they
        are the business."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.get(self.orders_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data},
            {self.related_order.id, self.completed_order.id},
        )

    def test_customer_can_create_order_from_offer_detail(self):
        """POST /api/orders/ Authenticated customer should be able to create
        an order from an offer detail."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.post(
            self.orders_url,
            {"offer_detail_id": self.offer_detail.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["customer_user"], self.customer_user.id)
        self.assertEqual(response.data["business_user"], self.business_user.id)
        self.assertEqual(response.data["status"], "in_progress")

    def test_create_order_requires_customer_profile(self):
        """POST /api/orders/ Authenticated business should not be able to create
        an order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.post(
            self.orders_url,
            {"offer_detail_id": self.offer_detail.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_requires_offer_detail_id(self):
        """POST /api/orders/ should return 400 Bad Request if offer_detail_id is missing."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.post(self.orders_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("offer_detail_id", response.data)

    def test_create_order_with_unknown_offer_detail_returns_404(self):
        """POST /api/orders/ should return 404 Not Found if the offer_detail_id does not exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.post(
            self.orders_url,
            {"offer_detail_id": 999999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_business_can_patch_order_status(self):
        """PATCH /api/orders/{id}/ Authenticated business should be able to update
        the status of an order they are related to."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.patch(
            self.order_detail_url,
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.related_order.refresh_from_db()
        self.assertEqual(self.related_order.status, "completed")

    def test_customer_cannot_patch_order_status(self):
        """PATCH /api/orders/{id}/ Authenticated customer should not be able to update
        the status of an order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        response = self.client.patch(
            self.order_detail_url,
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_order_with_invalid_status_returns_400(self):
        """PATCH /api/orders/{id}/ should return 400 Bad Request if the status is invalid."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.patch(
            self.order_detail_url,
            {"status": "cancelled"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_admin_can_delete_order(self):
        """DELETE /api/orders/{id}/ Authenticated admin should be able to delete an order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        response = self.client.delete(self.order_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=self.related_order.id).exists())

    def test_non_admin_cannot_delete_order(self):
        """DELETE /api/orders/{id}/ Authenticated non-admin should not be able to delete an order."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.business_token.key}")

        response = self.client.delete(self.order_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_count_requires_authentication(self):
        """GET /api/order-count/{business_user_id}/ unauthenticated users should receive
        a 401 Unauthorized response."""
        response = self.client.get(self.order_count_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_false_business_user_id_count_returns_in_progress_count(self):
        """GET /api/order-count/{business_user_id}/ should return 404 Not Found if the
        business user ID does not exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")
        url = self.order_count_url.format(99)
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_count_returns_in_progress_count(self):
        """GET /api/order-count/{business_user_id}/ should return the count of in-progress
        orders for the specified business user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        url = self.order_count_url.format(self.other_business_user.id)
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["order_count"], 1)

    def test_completed_order_count_returns_completed_count(self):
        """GET /api/completed-order-count/{business_user_id}/ should return the count of completed
        orders for the specified business user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.customer_token.key}")

        url = self.completed_order_count_url.format(self.business_user.id)
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completed_order_count"], 1)
