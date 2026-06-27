from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerByUserProfile(BasePermission):
    """
    - GET: all authenticated users.
    - PUT/PATCH: owner.
    """

    def has_permission(self, request, view):
        """Only authenticated users can make a purchase."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """- PATCH/PUT: only owner can"""
        user = request.user
        if user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return True

        return obj.user == user
