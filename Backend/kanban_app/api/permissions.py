from rest_framework import permissions
from rest_framework.permissions import BasePermission


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
