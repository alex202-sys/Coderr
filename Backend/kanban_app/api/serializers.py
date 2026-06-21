from rest_framework import serializers
from django.contrib.auth.models import User
from kanban_app.models import Offer, OfferDetail, Order


class OfferDetailUrlSerializer(serializers.ModelSerializer):
    """ "Serializer for listing OfferDetail objects with only ID and URL,
    used in GET responses of OfferSerializer."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating OfferDetail objects,
    used in PUT/PATCH requests of OfferSerializer."""

    # für update nur probiere
    # offer_type = serializers.CharField(required=True)

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]
        read_only_fields = ["offer"]


class OfferIdSerializer(serializers.ModelSerializer):
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    details = OfferDetailUrlSerializer(many=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
        ]
        # read_only_fields = ["offer"]

    def __init__(self, *args, **kwargs):
        """Switches the "details" field list
        from Sub-serializer       OfferDetailUrlSerializer
        to Sub-serializer         OfferDetailSerializer
        for PUT/PATCH methods."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method in ["PUT", "PATCH"]:
            self.fields["details"] = OfferDetailSerializer(
                many=True, context=self.context
            )

    def get_min_price(self, obj):
        prices = [detail.price for detail in obj.details.all()]
        return min(prices) if prices else 0

    def get_min_delivery_time(self, obj):
        times = [detail.delivery_time_in_days for detail in obj.details.all()]
        return min(times) if times else 0

    # def to_representation(self, instance):
    #     return super().to_representation(instance)

    def update(self, instance, validated_data):
        # 1. Hauptfelder des Offers aktualisieren (z.B. title, description, image)
        details_data = validated_data.pop("details", None)
        instance.title = validated_data.get("title", instance.title)
        instance.save()

        # 2. Verschachtelte Details aktualisieren, falls sie im Request enthalten sind
        if details_data is not None:
            # if object OfferDetail more than 1 in request "details"
            # for detail_data in details_data:
            detail_data = details_data[0]
            offer_type = detail_data.get("offer_type")
            if offer_type:
                # Suchen des existierenden Details dieses Offers anhand des offer_type
                try:
                    # Retrieve the object from the OfferDetail model via the
                    #  Offer.details.offer_type field.
                    detail_instance = instance.details.get(offer_type=offer_type)

                    # Einzelne Felder des Details aktualisieren
                    detail_instance.title = detail_data.get(
                        "title", detail_instance.title
                    )
                    detail_instance.revisions = detail_data.get(
                        "revisions", detail_instance.revisions
                    )
                    detail_instance.delivery_time_in_days = detail_data.get(
                        "delivery_time_in_days",
                        detail_instance.delivery_time_in_days,
                    )
                    detail_instance.price = detail_data.get(
                        "price", detail_instance.price
                    )
                    detail_instance.features = detail_data.get(
                        "features", detail_instance.features
                    )
                    detail_instance.save()

                except OfferDetail.DoesNotExist:
                    # Falls der Typ wider Erwarten nicht existiert, ignorieren oder optional erstellen
                    pass
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")

        if request.method in ["PATCH", "PUT"]:
            ret.pop("user")
            ret.pop("created_at")
            ret.pop("updated_at")
            ret.pop("min_price")
            ret.pop("min_delivery_time")

            actual_details = instance.details.all()
            full_details_serializer = OfferDetailSerializer(
                actual_details, many=True, context=self.context
            )
            ret["details"] = full_details_serializer.data

        return ret


class UserMinDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]


class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = UserMinDetailsSerializer(source="user", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        ]
        read_only_fields = ["user"]

    def get_min_price(self, obj):
        prices = [detail.price for detail in obj.details.all()]
        return min(prices) if prices else 0

    def get_min_delivery_time(self, obj):
        times = [detail.delivery_time_in_days for detail in obj.details.all()]
        return min(times) if times else 0

    def validate_details(self, value):
        if len(value) != 3:
            raise serializers.ValidationError(
                "An offer must contain exactly three details!"
            )
        return value

    def create(self, validated_data):
        """Generate an offer based on the request data, including
        the creation of multiple 'Model OfferDetail' objects."""
        details_data = validated_data.pop("details")

        request = self.context.get("request")
        if request and request.user:
            validated_data["user"] = request.user

        offer = Offer.objects.create(**validated_data)

        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)

        return offer

    def to_representation(self, instance):
        request = self.context.get("request")

        # Nutzen Sie den GET-spezifischen Aufbau, wenn es ein Listen-/Detail-Abruf ist
        if request and request.method == "GET":
            data = super().to_representation(instance)
            # Überschreibt die vollständigen Details mit der ID- und URL-Übersicht
            data["details"] = OfferDetailUrlSerializer(
                instance.details.all(), many=True
            ).data

            # Null-Werte zu leeren Strings konvertieren
            if data.get("image") is None:
                data["image"] = None
            return data

        # Standard representation for POST response (full details)
        data = super().to_representation(instance)
        if data.get("image") is None:
            data["image"] = None

        data.pop("user", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        return data


class OrdersOfferSerializer(serializers.ModelSerializer):

    offer_detail_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
            "offer_detail_id",
        ]
        # write_only_fields = ["offer_detail_id"]
        read_only_fields = [
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "customer_user",
            "business_user",
            # "created_at",
            # "updated_at",
        ]

    # def get_offer_detail_id(self, obj):
    #     if obj.offer_detail:
    #         return obj.offer_detail.id
    #     return None

    def create(self, validated_data):
        # offer_detail_id = self.context["request"].data.get("offer_detail_id")
        offer_detail_id = validated_data.pop("offer_detail_id")
        try:
            offerdetail = OfferDetail.objects.get(id=offer_detail_id)

        except OfferDetail.DoesNotExist:
            raise serializers.ValidationError(
                "OfferDetail with the given ID does not exist."
            )

        request = self.context.get("request")
        validated_data["offer_detail"] = offerdetail
        if request and request.user:
            validated_data["customer_user"] = request.user
        validated_data["business_user"] = offerdetail.offer.user
        validated_data["title"] = offerdetail.title
        validated_data["revisions"] = offerdetail.revisions
        validated_data["delivery_time_in_days"] = offerdetail.delivery_time_in_days
        validated_data["price"] = offerdetail.price
        validated_data["features"] = offerdetail.features
        validated_data["offer_type"] = offerdetail.offer_type
        # validated_data["status"] = Order.OrderStatus.in_progress
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Prevent updates to offer_detail and user fields"""
        if "status" in validated_data:
            instance.status = validated_data.pop("status", None)
        return super().update(instance, validated_data)


class OrdersCountSerializer(serializers.Serializer):
    """The number of active orders (status: in_progress or completed) for the business user"""

    order_count = serializers.SerializerMethodField(read_only=True, default=0)

    def get_order_count(self, obj):
        status_filter = self.context.get("status_filter", None)
        return Order.objects.filter(business_user=obj, status=status_filter).count()
