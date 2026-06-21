from rest_framework import viewsets, filters, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Min
from .permissions import (
    IsBusinessUserOrReadOnly,
    OfferIdViewSetIsOwnerOrReadOnly,
    IsUserCustomerOrBusinnesOrAdmin,
)
from kanban_app.api.serializers import (
    OfferSerializer,
    OfferIdSerializer,
    OfferDetailSerializer,
    OrdersCountSerializer,
    OrdersOfferSerializer,
)
from kanban_app.models import Offer, OfferDetail, Order

# class OfferIdViewSet(viewsets.ModelViewSet):
#     queryset = Offer.objects.all()
#     serializer_class = OfferIdSerializer
#     permission_classes = [OfferIdViewSetIsOwnerOrReadOnly]
#     # Nur Ersteller des Angebotes können dies löschen.


class OfferDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    # permission_classes = [OfferIdViewSetIsOwnerOrReadOnly]


class OfferCustomPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 30


class OfferViewSet(viewsets.ModelViewSet):
    """/api/offers/
    GET - Query Parameters: creator_id, min_price, max_delivery_time, ordering
        search, page_size. No Permissions required.
    POST- An Offer must contain three OfferDetail.
        Only users of type 'business' are allowed to create offers.
    """

    # fetches all offers and linked user profiles and details (OfferDetail)
    queryset = (
        Offer.objects.all()
        .prefetch_related("details", "user")
        .select_related("user__profile")
    )
    # serializer_class = OfferSerializer
    # permission_classes = [IsBusinessUserOrReadOnly]
    pagination_class = OfferCustomPagination

    # Nur noch die Standard-Filter für die Suche nutzen
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
        print("get_permissions self.action: ", self.action)
        if self.action == "list" or self.action == "create":
            return [IsBusinessUserOrReadOnly()]
        elif self.action == "retrieve":
            print("get_permissions retrieve")
            return [IsAuthenticated()]
        # self.action == "retrieve" or self.action == "update"
        # or self.action == "partial_update" or self.action == "destroy"
        return [OfferIdViewSetIsOwnerOrReadOnly()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list" or self.action == "create":
            # if 1 == 1:
            print("OfferViewSet get_queryset queryset", queryset)
            params = self.request.query_params
            print("OfferViewSet get_queryset params:", params)

            # 1. Filtern nach Schöpfer/Ersteller (?creator_id=...)
            creator_id = params.get("creator_id")
            if creator_id:
                queryset = queryset.filter(user_id=creator_id)

            # 2. Filtern nach Mindestpreis (?min_price=...)
            min_price = params.get("min_price")
            if min_price:
                print("min_price: ", min_price)
                queryset = queryset.filter(details__price__lte=min_price)
                # queryset = queryset.filter(details__price__gte=min_price).distinct()

            # 3. Filtern nach maximaler Lieferzeit (?max_delivery_time=...)
            max_delivery_time = params.get("max_delivery_time")
            if max_delivery_time:
                queryset = queryset.filter(
                    details__delivery_time_in_days__lte=max_delivery_time
                )

            # 4. Manuelle Sortierung (?ordering=...)
            ordering = params.get("ordering")
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


class OrdersCountViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        business_user = get_object_or_404(User, id=pk)  # Import aus django.shortcuts
        status_filter = "in_progress"
        serializer = OrdersCountSerializer(
            business_user, context={"status_filter": status_filter}
        )  # User als Objekt übergeben
        print("OrdersCountViewSet get_count serializer.data: ", serializer.data)
        return Response(serializer.data)


class OrdersCompletedCountViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        business_user = get_object_or_404(User, id=pk)  # Import aus django.shortcuts
        status_filter = "completed"
        serializer = OrdersCountSerializer(
            business_user, context={"status_filter": status_filter}
        )  # User als Objekt übergeben
        print(
            "OrdersCompletedCountViewSet get_count serializer.data: ", serializer.data
        )
        return Response(serializer.data)
