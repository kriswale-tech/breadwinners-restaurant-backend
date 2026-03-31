import json

from django.db.models import Prefetch
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.db import transaction
from .models import Package, PackageItem, Product, ProductCategory
from .serializers import (
    PackageSerializer,
    ProductCategoryDetailSerializer,
    ProductCategorySerializer,
    ProductSerializer,
)


# def _parse_package_items_payload(data):
#     """Parse `items` from multipart form (JSON string) or leave list as-is."""
#     if hasattr(data, "dict"):
#         data = data.dict()
#     items = data.get("items")
#     if items is not None:
#         if isinstance(items, str):
#             try:
#                 items = json.loads(items)
#             except json.JSONDecodeError:
#                 raise ValidationError({"items": "Invalid JSON for items."})
#         if not isinstance(items, list):
#             raise ValidationError({"items": "Items must be a list."})
#         data["items"] = items
#     return data

def _parse_package_items_payload(data):
    """Parse `items` from multipart form (JSON string) or leave list as-is."""
    # Normalize to a plain dict; QueryDict cannot safely hold nested list/dict values.
    if hasattr(data, "keys") and hasattr(data, "get"):
        normalized = {key: data.get(key) for key in data.keys()}
    else:
        normalized = dict(data)

    items = normalized.get("items")

    if items is None:
        return normalized

    # Handle string input (multipart/form-data)
    if isinstance(items, str):
        if not items.strip():
            items = []
        else:
            try:
                items = json.loads(items)
            except json.JSONDecodeError:
                raise ValidationError({"items": "Invalid JSON for items."})

    # Ensure it's a list
    if not isinstance(items, list):
        raise ValidationError({"items": "Items must be a list."})

    # Ensure each item is a dict
    if not all(isinstance(item, dict) for item in items):
        raise ValidationError({"items": "Each item must be an object."})

    normalized["items"] = items
    return normalized


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]


class ProductCategoryViewSet(ModelViewSet):
    queryset = ProductCategory.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductCategoryDetailSerializer
        if self.action in ("update", "partial_update"):
            return ProductCategorySerializer
        return ProductCategorySerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]


class PackageViewSet(ModelViewSet):
    queryset = (
        Package.objects.all()
        .prefetch_related(
            Prefetch(
                "items",
                queryset=PackageItem.objects.select_related("product"),
            )
        )
    )
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        data = _parse_package_items_payload(request.data.copy())
        
        with transaction.atomic():
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            # Re-serialize the saved instance so nested items are returned from DB state.
            response_serializer = self.get_serializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        data = _parse_package_items_payload(request.data.copy())
        
        with transaction.atomic():
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            # Mirror UpdateModelMixin behavior: clear stale prefetched relation cache.
            if getattr(instance, "_prefetched_objects_cache", None):
                instance._prefetched_objects_cache = {}
            response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data)


class ProductStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "products": Product.objects.count(),
                "categories": ProductCategory.objects.count(),
                "packages": Package.objects.count(),
            },
            status=status.HTTP_200_OK,
        )
