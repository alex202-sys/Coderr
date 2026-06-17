from rest_framework.permissions import BasePermission, SAFE_METHODS

# from rest_framework.exceptions import PermissionDenied, NotFound


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
        #     else:
        #         raise PermissionDenied(
        #             detail="403: Forbidden. Only the owner of the board can delete it.",
        #         )

        # # all othe methods except DELETE: PATCH, PUT, GET, HEAD, OPTIONS
        # if obj.owner == user or user in obj.member.all():
        #     return True
        # else:
        #     raise PermissionDenied(
        #         "403:     Forbidden. The user must be either the owner or a member of the board."
        #     )
        # return False
