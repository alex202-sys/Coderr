from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Min
from django.db.models import Q
from rest_framework import viewsets, filters, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from kanban_app.models import Offer, OfferDetail, Order, Review
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


class OfferDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """ViewSet for retrieving OfferDetail objects."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer


class OfferCustomPagination(PageNumberPagination):
    """Custom pagination class for the OfferViewSet.
    Allows clients to specify the number of items
    per page using the 'page_size' query parameter"""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 30

    def get_page_size(self, request):
        """Override the default get_page_size method to handle the 'page_size' query parameter.
        If the 'page_size' parameter is provided, it will be validated and used to determine
        the number of items per page. If the parameter is not provided or is invalid,
        the default page size will be used."""
        page_size_param = request.query_params.get(self.page_size_query_param)
        print(f"Received page_size parameter: {page_size_param}")  # Debugging line
        if page_size_param:
            try:
                page_size_val = int(page_size_param)
                if page_size_val > self.max_page_size:
                    return self.max_page_size
                if page_size_val <= 0:
                    return self.page_size

                return page_size_val
            except ValueError:
                raise ValidationError(
                    {
                        self.page_size_query_param: "This parameter must be a valid integer.."
                    }
                )

        return super().get_page_size(request)


class OfferViewSet(viewsets.ModelViewSet):
    """
    /api/offers/
    GET - Query Parameters: creator_id, min_price, max_delivery_time, ordering
        search, page_size. No Permissions required.
    POST- An Offer must contain three OfferDetail.
        Only users of type 'business' are allowed to create offers.
    """

    # Simultaneously with Object Offer, DRF takes linked object details and user
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
            return OfferSerializer

        return None

    def get_permissions(self):
        if self.action == "list" or self.action == "create":
            return [IsBusinessUserOrReadOnly()]
        elif self.action == "retrieve":
            return [IsAuthenticated()]
        return [OfferIdViewSetIsOwnerOrReadOnly()]

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                calc_min_price=Min("details__price"),
                calc_max_delivery=Min("details__delivery_time_in_days"),
            )
        )

        if self.action in ["list", "create"]:

            query_serializer = OfferQueryParametersSerializer(
                data=self.request.query_params
            )
            # 2. Validate! If, for example, max_delivery_time="test",
            # DRF aborts IMMEDIATELY here and sends a 400 status to the frontend.
            if query_serializer.is_valid(raise_exception=True):
                validated_params = query_serializer.validated_data

                creator_id = validated_params.get("creator_id")
                if creator_id:
                    queryset = queryset.filter(user_id=creator_id)

                min_price = validated_params.get("min_price")
                if min_price is not None:
                    queryset = queryset.filter(calc_min_price__gte=min_price).distinct()

                max_delivery_time = validated_params.get("max_delivery_time")
                if max_delivery_time is not None:
                    queryset = queryset.filter(
                        calc_max_delivery__lte=max_delivery_time
                    ).distinct()

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
    """ViewSet for managing orders on the platform."""

    queryset = Order.objects.all()
    serializer_class = OrdersOfferSerializer
    permission_classes = [IsUserCustomerOrBusinnesOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        if user.is_staff or user.is_superuser:
            return queryset
        if self.action in ["list", "retrieve"]:
            return queryset.filter(
                Q(customer_user=user) | Q(business_user=user)
            ).distinct()
        return queryset


class OrdersCountViewSet(viewsets.GenericViewSet):
    """ViewSet for counting orders based on their status.
    GET - Returns the count of orders for a specific business user.
    """

    queryset = Order.objects.all()
    serializer_class = OrdersCountSerializer

    def get_queryset(self, pk=None):
        queryset = super().get_queryset()
        pk = self.kwargs.get("pk")
        if self.action == "retrieve":
            business_user = get_object_or_404(User, id=pk)
            queryset = queryset.filter(
                business_user=business_user, status="in_progress"
            )
            return queryset
        return queryset.none()

    def retrieve(self, request, pk=None):
        business_user = get_object_or_404(User, id=pk)
        queryset = self.get_queryset()
        orders_count = queryset.count()
        serializer = self.get_serializer({"order_count": orders_count})
        return Response(serializer.data)


class OrdersCompletedCountViewSet(viewsets.ViewSet):
    """ViewSet for counting completed orders for a specific business user.
    GET - Returns the count of completed orders for a specific business user.
    """

    def retrieve(self, request, pk=None):
        queryset = Order.objects.all()
        business_user = get_object_or_404(User, id=pk)  # Import aus django.shortcuts
        queryset = queryset.filter(business_user=business_user, status="completed")
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
        # Set context for the serializer
        self.get_serializer_context()["request"] = self.request
        serializer.save(reviewer=user)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
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
