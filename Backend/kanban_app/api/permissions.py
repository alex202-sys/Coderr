from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions
from kanban_app.models import Review


class OfferIdViewSetIsOwnerOrReadOnly(BasePermission):
    """Only the creator of an offer can delete it.
    GET is allowed for all users."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif obj.user == request.user:
            return True

        return False


class IsBusinessUserOrReadOnly(BasePermission):
    """POST/PUT/PATCH only user with profil-type business are allowed.
    GET can same user"""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            getattr(request.user, "profile", None)
            and request.user.profile.type == "business"
        )


class IsUserCustomerOrBusinnesOrAdmin(BasePermission):
    """
    - GET This endpoint returns only orders associated with the logged-in user,
      either as a customer or as a business partner.
      user either as a customer or as a business partner.
    - POST/orders/  - now requires a customer profile
    - PATCH /orders/{id}/ now requires the related business user
    - DELETE /orders/{id}/ now requires admin/staff
    """

    def has_permission(self, request, view):
        """GET This endpoint returns only orders associated with the
        logged-in user, either as a customer or as a business partner.
        user either as a customer or as a business partner.
        POST/orders/  - now requires a customer profile"""

        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        if request.method == "POST":
            return (
                getattr(request.user, "profile", None)
                and request.user.profile.type == "customer"
            )

        if request.method in ["GET", "HEAD", "OPTIONS", "PATCH"]:

            return getattr(request.user, "profile", None) and (
                request.user.profile.type == "business"
                or request.user.profile.type == "customer"
            )

        return False

    def has_object_permission(self, request, view, obj):
        """PATCH /orders/{id}/ now requires the related business user
        DELETE /orders/{id}/ now requires admin/staff"""

        if request.method == "DELETE" and (
            request.user.is_staff or request.user.is_superuser
        ):
            return True
        elif request.method == "PATCH":
            if (
                getattr(request.user, "profile", None)
                and request.user.profile.type == "business"
            ):
                return True
        return False


class IsOwnerCustomerOrReadOnly(permissions.BasePermission):
    """
    - POST only user with type customer allow to create reviews for orders they have placed.
    - PATCH/ DELETE only owner by review allow to update reviews.
    - GET only authenticated users are allowed to read reviews.
    """

    def has_permission(self, request, view):
        """POST only user with type customer allow to create reviews for business user.
        GET  only authenticated users are allowed to read reviews."""

        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == "POST":
            if not (
                (
                    getattr(request.user, "profile", None)
                    and request.user.profile.type == "customer"
                )
            ):
                raise PermissionDenied(
                    detail="403: Forbidden. Only users with a customer profile can create reviews.",
                )
        return True

    def has_object_permission(self, request, view, obj):
        """GET only authenticated users are allowed to read reviews.
        PATCH/DELETE only owner by review allow to update or delete
        reviews they have created."""
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ["PATCH", "DELETE"]:
            return obj.reviewer == request.user

        return False
