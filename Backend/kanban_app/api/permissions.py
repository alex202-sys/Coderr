from rest_framework import permissions
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from kanban_app.models import Review


class OfferIdViewSetIsOwnerOrReadOnly(BasePermission):
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
    - GET Only authenficierte users
    - POST - Only authenficierte users with profil-type 'customer'
    - PATCH - Only authenficierte users with profil-type 'business'
    - DELETE - only staff or admin are allowed to delete orders.
    -
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        print(
            "IsUserCustomerOrBusinnesOrAdmin has_permission request.method: ",
            request.method,
        )
        return True

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE" and (
            request.user.is_staff or request.user.is_superuser
        ):
            return True
        elif (
            request.method == "PATCH"
            and getattr(request.user, "profile", None)
            and request.user.profile.type == "business"
        ):
            return True
        elif (
            request.method == "POST"
            and getattr(request.user, "profile", None)
            and request.user.profile.type == "customer"
        ):
            print("IsUserCustomerOrBusinnesOrAdmin has_object_permission POST")
            return True
        elif request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return False


class IsOwnerCustomerOrReadOnly(permissions.BasePermission):
    """
    - POST only user with type customer allow to create reviews for orders they have placed.
    - PATCH/ DELETE only owner by review allow to update reviews.
    - GET only authenticated users are allowed to read reviews.
    """

    def has_permission(self, request, view):
        print(
            "IsOwnerCustomerOrReadOnly has_permission request.method: ", request.method
        )
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

            reviewer = request.user
            business_user_id = request.data.get("business_user")
            if Review.objects.filter(
                business_user=business_user_id, reviewer=reviewer
            ).exists():
                raise PermissionDenied(
                    detail="403: Forbidden. A user can submit only one review per business profile.",
                )

        return True

    def has_object_permission(self, request, view, obj):
        print(
            "IsOwnerCustomerOrReadOnly has_object_permission request.method: ",
            request.method,
        )
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ["PATCH", "DELETE"]:
            return obj.reviewer == request.user

        return False
        # elif request.method == "POST":
        #     print("IsOwnerCustomerOrReadOnly has_object_permission POST")

        #     if (
        #         getattr(request.user, "profile", None)
        #         and request.user.profile.type == "customer"
        #     ):
        #         reviewer = request.user
        #         business_user_id = request.data.get("business_user")
        #         print(
        #             "IsOwnerCustomerOrReadOnly has_object_permission POST reviewer: ",
        #             reviewer,
        #         )
        #         print(
        #             "IsOwnerCustomerOrReadOnly has_object_permission POST business_user: ",
        #             business_user_id,
        #         )
        #         if Review.objects.filter(
        #             business_user=obj.business_user_id, reviewer=request.user
        #         ).exists():
        #             raise PermissionDenied(
        #                 detail="403: Forbidden. A user can submit only one review per business profile.",
        #             )
