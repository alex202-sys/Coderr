from django.db import models
from django.contrib.auth.models import User


class Offer(models.Model):
    """Each offer typically have three OfferDetail — Basic, Standard, and Premium—specifying
    details such as price and delivery time; only business users can create these offers.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers")
    title = models.CharField(max_length=255)  # unique=True
    # image = models.ImageField(upload_to="offers/", blank=True, null=True)
    image = models.FileField(upload_to="offers/", blank=True, null=True, default=None)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    """Details for each offer (three tiers per offer):
    offer type (Basic, Standard, Premium), price,
    delivery time, and more."""

    class OfferType(models.TextChoices):
        BASIC = "basic", "Basic"
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
    title = models.CharField(max_length=155, default="")
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(
        default=list
    )  # Speichert die Liste von Strings (z.B. ["Logo Design", "Visitenkarte"])
    offer_type = models.CharField(
        max_length=10, choices=OfferType.choices, default=OfferType.BASIC
    )

    def __str__(self):
        return f"{self.offer.title} - {self.offer_type}"


class Order(models.Model):

    class OfferType(models.TextChoices):
        BASIC = "basic", "Basic"
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    class OrderStatus(models.TextChoices):
        in_progress = "in_progress", "In Progress"
        completed = "completed", "Completed"

    # offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
    offer_detail = models.ForeignKey(
        OfferDetail, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    customer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customerorders"
    )
    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="businessorders"
    )
    title = models.CharField(max_length=155, default="")
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(
        default=list
    )  # Speichert die Liste von Strings (z.B. ["Logo Design", "Visitenkarte"])
    offer_type = models.CharField(
        max_length=10, choices=OfferType.choices, default=OfferType.BASIC
    )
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.in_progress
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.offer_type}"
