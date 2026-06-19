from django.contrib import admin
from .models import UserProfile
from kanban_app.models import Offer, OfferDetail
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.
# admin.site.register(UserProfile)
# admin.site.register(Offer)
# admin.site.register(OfferDetail)
# Register your models here.

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # list_display vom originalen UserAdmin holen und 'id' ganz vorne einfügen
    list_display = ("id", "get_user_profile_link") + UserAdmin.list_display

    # Optional: Die ID auch anklickbar machen, um den User zu öffnen
    list_display_links = ("id", "username")

    @admin.display(ordering="user__profile", description="Profile")
    def get_user_profile_id(self, obj):
        if obj.profile:
            return obj.profile.id
        return "-"

    @admin.display(description="Profile ID")
    def get_user_profile_link(self, obj):
        # HIER nutzen wir jetzt "profile", weil es so in Ihrem Model steht!
        if hasattr(obj, "profile") and obj.profile:
            profile_id = obj.profile.id

            # Tauschen Sie 'ihre_app_name' gegen den echten Namen Ihres App-Ordners aus
            url = reverse("admin:auth_app_userprofile_change", args=[profile_id])

            return format_html('<a href="{}">Profile #{}</a>', url, profile_id)

        return "-"


@admin.register(UserProfile)
class UserProfile(admin.ModelAdmin):
    list_display = ("id", "user", "get_user_id", "type")
    list_display_links = ("id", "user")

    @admin.display(ordering="user__id", description="User ID")
    def get_user_id(self, obj):
        if obj.user:
            return obj.user.id
        return "-"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):

    # 'id' wird hier als erste Spalte hinzugefügt
    list_display = ("id", "title", "description")

    # Optional: Macht die ID anklickbar, um das Objekt zu öffnen
    list_display_links = ("id", "title")


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):

    # 'id' wird hier als erste Spalte hinzugefügt
    list_display = ("id", "offer", "title")

    # Optional: Macht die ID anklickbar, um das Objekt zu öffnen
    list_display_links = ("id", "offer", "title")
