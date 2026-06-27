from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OfferViewSet,
    OfferDetailViewSet,
    OrdersOfferViewSet,
    OrdersCountViewSet,
    OrdersCompletedCountViewSet,
    BaseInfoViewSet,
    ReviewViewSet,
)

router = DefaultRouter()
router.register(r"offers", OfferViewSet, basename="offer")  # "offer"
router.register(r"offerdetails", OfferDetailViewSet, basename="offer-detail")
router.register(r"orders", OrdersOfferViewSet, basename="order")
router.register(r"order-count", OrdersCountViewSet, basename="order-count")
router.register(
    r"completed-order-count",
    OrdersCompletedCountViewSet,
    basename="completed-order-count",
)
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"base-info", BaseInfoViewSet, basename="base-info")

urlpatterns = [
    path("", include(router.urls)),
]
