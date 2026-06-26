from rest_framework import viewsets, filters, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

# from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Min
from django.db.models import Q
from .permissions import (
    IsBusinessUserOrReadOnly,
    OfferIdViewSetIsOwnerOrReadOnly,
    IsUserCustomerOrBusinnesOrAdmin,
    IsOwnerCustomerOrReadOnly,
)
from kanban_app.api.serializers import (
    BaseInfoSerializer,
    OfferSerializer,
    OfferIdSerializer,
    OfferDetailSerializer,
    OrdersCountSerializer,
    OrdersOfferSerializer,
    ReviewSerializer,
    OfferQueryParametersSerializer,
)
from kanban_app.models import Offer, OfferDetail, Order, Review


class OfferDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer


class OfferCustomPagination(PageNumberPagination):
    """Custom pagination class for the OfferViewSet.
    Allows clients to specify the number of items
    per page using the 'page_size' query parameter"""

    page_size_query_param = "page_size"
    max_page_size = 30

    def get_page_size(self, request):
        """validies the page_size query parameter to ensure it's a valid integer.
        If the parameter is invalid, a ValidationError is raised."""
        page_size_param = request.query_params.get(self.page_size_query_param)
        if page_size_param:
            try:
                return int(page_size_param)
            except ValueError:
                raise ValidationError(
                    {
                        self.page_size_query_param: "This parameter must be a valid integer.."
                    }
                )

        return super().get_page_size(request)


class OfferViewSet(viewsets.ModelViewSet):
    """/api/offers/
    GET - Query Parameters: creator_id, min_price, max_delivery_time, ordering
        search, page_size. No Permissions required.
    POST- An Offer must contain three OfferDetail.
        Only users of type 'business' are allowed to create offers.
    """

    queryset = (
        Offer.objects.all()
        .prefetch_related("details", "user")
        .select_related("user__profile")
    )

    pagination_class = OfferCustomPagination

    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]

    def get_serializer_class(self, *args, **kwargs):
        if (
            self.action == "retrieve"
            or self.action == "update"
            or self.action == "partial_update"
            or self.action == "destroy"
        ):
            return OfferIdSerializer

        if self.action == "list" or self.action == "create":
            # context["request"] = self.request
            return OfferSerializer

        return None

    def get_permissions(self):
        if self.action == "list" or self.action == "create":
            return [IsBusinessUserOrReadOnly()]
        elif self.action == "retrieve":
            return [IsAuthenticated()]
        return [OfferIdViewSetIsOwnerOrReadOnly()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ["list", "create"]:
            # if 1 == 1:
            # params = self.request.query_params

            query_serializer = OfferQueryParametersSerializer(
                data=self.request.query_params
            )
            # 2. Validieren! Wenn z.B. max_delivery_time="test" ist,
            # bricht DRF hier SOFORT ab und sendet Status 400 an das Frontend.
            query_serializer.is_valid(raise_exception=True)
            validated_params = query_serializer.validated_data

            creator_id = validated_params.get("creator_id")
            if creator_id:
                queryset = queryset.filter(user_id=creator_id)

            min_price = validated_params.get("min_price")
            if min_price:
                queryset = queryset.filter(details__price__lte=min_price)

            max_delivery_time = validated_params.get("max_delivery_time")
            if max_delivery_time:
                queryset = queryset.filter(
                    details__delivery_time_in_days__lte=max_delivery_time
                )
            queryset = queryset.distinct()

            # try:
            #     # 1. Filtern nach Schöpfer/Ersteller (?creator_id=...)
            #     creator_id = params.get("creator_id")
            #     if creator_id:
            #         queryset = queryset.filter(user_id=creator_id)

            #     # 2. Filtern nach Mindestpreis (?min_price=...)
            #     min_price = params.get("min_price")
            #     if min_price:
            #         queryset = queryset.filter(details__price__lte=min_price)
            #         # queryset = queryset.filter(details__price__gte=min_price).distinct()

            #     # 3. Filtern nach maximaler Lieferzeit (?max_delivery_time=...)
            #     max_delivery_time = params.get("max_delivery_time")
            #     print("OfferViewSet von requestmax_delivery_time: ", max_delivery_time)
            #     if max_delivery_time:
            #         queryset = queryset.filter(
            #             details__delivery_time_in_days__lte=max_delivery_time
            #         )
            # except ValueError:
            #     raise ValidationError({"parameters": "Invalid request parameters."})

            # # Duplikate durch JOINs entfernen
            # queryset = queryset.distinct()
            # 4. Manuelle Sortierung (?ordering=...)
            ordering = validated_params.get("ordering")
            if ordering == "min_price":
                queryset = queryset.annotate(
                    lowest_price=Min("details__price")
                ).order_by("lowest_price")
            elif ordering == "-min_price":
                queryset = queryset.annotate(
                    lowest_price=Min("details__price")
                ).order_by("-lowest_price")
            elif ordering == "updated_at":
                queryset = queryset.order_by("updated_at")
            elif ordering == "-updated_at":
                queryset = queryset.order_by("-updated_at")
            else:
                # Falls kein Ordering-Parameter übergeben wurde, zwingend nach ID sortieren!
                queryset = queryset.order_by("id")

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrdersOfferViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersOfferSerializer
    permission_classes = [IsUserCustomerOrBusinnesOrAdmin]

    # KI falsch erstrelt
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_staff or user.is_superuser:
            return queryset
        if self.action in ["list", "retrieve"]:
            # print("OrdersOfferViewSet get_queryset user: ", user)
            return queryset.filter(
                Q(customer_user=user) | Q(business_user=user)
            ).distinct()
        return queryset


class OrdersCountViewSet(viewsets.GenericViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrdersCountSerializer

    def get_queryset(self, pk=None):
        queryset = super().get_queryset()
        pk = self.kwargs.get("pk")
        # print("OrdersCountViewSet get_queryset pk: ", pk)
        # print("OrdersCountViewSet get_queryset action: ", self.action)
        if self.action == "retrieve":
            # business_user_id = self.request.query_params.get("business_user_id")
            business_user = get_object_or_404(
                User, id=pk
            )  # Import aus django.shortcuts
            # if business_user_id:
            # print("OrdersCountViewSet get_queryset business_user: ", business_user)
            queryset = queryset.filter(
                business_user=business_user, status="in_progress"
            )
            # print("OrdersCountViewSet get_queryset queryset: ", queryset)
            return queryset
        return queryset.none()

    def retrieve(self, request, pk=None):
        # business_user = get_object_or_404(User, id=pk)  # Import aus django.shortcuts
        # business_user_id = self.request.query_params.get("business_user_id")
        business_user = get_object_or_404(User, id=pk)
        # print("OrdersCountViewSet retrieve business_user: ", business_user)
        # print("OrdersCountViewSet retrieve business_user: ", business_user)
        # status_filter = "in_progress"
        queryset = self.get_queryset()
        orders_count = queryset.count()
        serializer = self.get_serializer({"order_count": orders_count})
        # print("OrdersCountViewSet get_count serializer.data: ", serializer.data)
        return Response(serializer.data)


class OrdersCompletedCountViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        queryset = Order.objects.all()
        business_user = get_object_or_404(User, id=pk)  # Import aus django.shortcuts
        queryset = queryset.filter(business_user=business_user, status="completed")
        # status_filter = "completed"
        # serializer = OrdersCountSerializer(
        #     business_user, context={"status_filter": status_filter}
        # )
        data = {"order_count": queryset.count()}
        serializer = OrdersCountSerializer(data)

        return Response(
            {"completed_order_count": serializer.data.get("order_count", 0)}
        )


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews on the platform.
    - POST: Only users with a customer profile can
    create reviews for business users.
    - PATCH/DELETE: Only the owner of the review can update or delete it.
    - GET: Only authenticated users are allowed to read reviews."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerCustomerOrReadOnly]

    ordering_fields = ["updated_at", "rating"]

    def perform_create(self, serializer):
        user = self.request.user

        self.get_serializer_context()[
            "request"
        ] = self.request  # Kontext für den Serializer setzen
        serializer.save(reviewer=user)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            # Optional: Filtere Bewertungen basierend auf Query-Parametern (z.B. business_user_id)
            # business_user_id = self.request.query_params.get("business_user_id")
            params = self.request.query_params
            business_user_id = params.get("business_user_id")
            if business_user_id:
                queryset = queryset.filter(business_user_id=business_user_id)
            reviewer_id = params.get("reviewer_id")
            if reviewer_id:
                queryset = queryset.filter(reviewer_id=reviewer_id)

            ordering = params.get("ordering")
            if ordering == "updated_at":
                queryset = queryset.order_by("updated_at")
            elif ordering == "-updated_at":
                queryset = queryset.order_by("-updated_at")
            elif ordering == "rating":
                queryset = queryset.order_by("rating")
            elif ordering == "-rating":
                queryset = queryset.order_by("-rating")

        return queryset


class BaseInfoViewSet(viewsets.ViewSet):
    """ViewSet for the platform's basic information, such as
    the total number of reviews, average rating, number of
    registered business profiles, and number of available offers.
    GET - No permissions required, as this information is intended
    to be publicly accessible.."""

    permission_classes = [AllowAny]

    def list(self, request):
        serializer = BaseInfoSerializer(data={})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
