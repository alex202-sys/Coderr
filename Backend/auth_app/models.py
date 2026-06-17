from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Model representing a user's profile."""

    class UserType(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        BUSINESS = "business", "Business"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    type = models.CharField(
        max_length=10, choices=UserType.choices, default=UserType.CUSTOMER
    )
    file = models.FileField(upload_to="profiles/", blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100, blank=True, default="")
    tel = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ["email", "type"]

    def __str__(self):
        return f"Profile of {self.user.username}"

    # @property
    # def fullname(self):
    #     """Returns the full name of the user by combining the first and last name."""

    #     return f"{self.user.first_name} {self.user.last_name}".strip()


# Create your models here.
