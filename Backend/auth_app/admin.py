from django.contrib import admin
from .models import UserProfile
from kanban_app.models import Offer, OfferDetail
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin view for User model with profile link."""

    # Get list_display from the original UserAdmin and insert 'id' at the very beginning
    list_display = ("id", "get_user_profile_link") + UserAdmin.list_display

    # Optional: Make the ID clickable as well to open the user
    list_display_links = ("id", "username")

    @admin.display(ordering="user__profile", description="Profile")
    def get_user_profile_id(self, obj):
        if obj.profile:
            return obj.profile.id
        return "-"

    @admin.display(description="Profile ID")
    def get_user_profile_link(self, obj):
        # Here we use "profile" because that is how it is defined in your model!
        if hasattr(obj, "profile") and obj.profile:
            profile_id = obj.profile.id

            # Replace 'auth_app' with the actual name of your app folder
            url = reverse("admin:auth_app_userprofile_change", args=[profile_id])

            return format_html('<a href="{}">Profile #{}</a>', url, profile_id)

        return "-"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin view for UserProfile."""

    list_display = ("id", "user", "get_user_id", "type")
    list_display_links = ("id", "user")

    @admin.display(ordering="user__id", description="User ID")
    def get_user_id(self, obj):
        if obj.user:
            return obj.user.id
        return "-"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin view for Offer."""

    # 'id' is added here as the first column
    list_display = ("id", "title", "description")

    # Optional: Make the ID clickable to open the object
    list_display_links = ("id", "title")


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin view for OfferDetail."""

    # 'id' is added here as the first column
    list_display = ("id", "offer", "title")

    # Optional: Make the ID clickable to open the object
    list_display_links = ("id", "offer", "title")
