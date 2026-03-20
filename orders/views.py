from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from orders.models import Order
from orders.serializers import OrderListCreateSerializer, OrderDetailSerializer
from permissions.shop_permissions import IsShopMember
from django.db.models import Prefetch
from orders.models import OrderItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# Create your views here.
class OrderView(ListCreateAPIView):
    serializer_class = OrderListCreateSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]

        return (
            Order.objects
            .filter(shop_id=shop_id)
            .select_related("shop")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product", "package")
                )
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(shop_id=self.kwargs["shop_id"])

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated(), IsShopMember()]


class OrderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsShopMember]
    lookup_field = "id"
    lookup_url_kwarg = "order_id"

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]

        return (
            Order.objects
            .filter(shop_id=shop_id)
            .select_related("shop")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product", "package")
                )
            )
            .order_by("-created_at")
        )


class OrderStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]
        return Order.objects.filter(shop_id=shop_id)

    def get(self, request, *args, **kwargs):
        orders = self.get_queryset()
        
        pending_orders = orders.filter(status=Order.StatusChoices.PENDING)
        confirmed_orders = orders.filter(status=Order.StatusChoices.CONFIRMED)
        delivered_orders = orders.filter(status=Order.StatusChoices.DELIVERED)
        done_orders = orders.filter(status=Order.StatusChoices.DONE)
        cancelled_orders = orders.filter(status=Order.StatusChoices.CANCELLED)

        return Response({
            "pending": pending_orders.count(),
            "confirmed": confirmed_orders.count(),
            "delivered": delivered_orders.count(),
            "done": done_orders.count(),
            "cancelled": cancelled_orders.count()
        }, status=status.HTTP_200_OK)