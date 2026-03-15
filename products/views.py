from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Product, ProductCategory, Package, PackageItem
from .serializers import ProductSerializer, ProductCategorySerializer, ProductCategoryDetailSerializer, PackageSerializer
from rest_framework.viewsets import ModelViewSet
from permissions.shop_permissions import IsShopMember
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
import json


# handles all product routes for a specific shop, including listing, creating, updating, and deleting products
class ShopProductsView(APIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]
        if not shop_id:
            raise ValidationError({"detail": "Shop ID is required"})
        return Product.objects.filter(shop_id=shop_id)

    def get_permissions(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsShopMember()]

    def get(self, request, shop_id, product_id=None):
        queryset = self.get_queryset()
        if product_id is not None:
            product = get_object_or_404(queryset, pk=product_id)
            serializer = self.serializer_class(product, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.serializer_class(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, shop_id):
        data = request.data.copy()
        data["shop_id"] = shop_id
        serializer = self.serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, shop_id, product_id):
        product = get_object_or_404(self.get_queryset(), pk=product_id)
        data = request.data.copy()
        data["shop_id"] = shop_id
        serializer = self.serializer_class(product, data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, shop_id, product_id):
        product = get_object_or_404(self.get_queryset(), pk=product_id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# for viewing all products regardless of shop
class ProductView(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ShopProductCategoriesView(APIView):
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        shop_id = self.kwargs["shop_id"]
        if not shop_id:
            raise ValidationError({"detail": "Shop ID is required"})
        return ProductCategory.objects.filter(shop_id=shop_id)

    def get_permissions(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsShopMember()]

    def get(self, request, shop_id, product_category_id=None):
        queryset = self.get_queryset()
        if product_category_id is not None:
            category = get_object_or_404(queryset, pk=product_category_id)
            serializer = ProductCategoryDetailSerializer(category, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.serializer_class(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, shop_id):
        data = request.data.copy()
        data["shop_id"] = shop_id
        serializer = self.serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, shop_id, product_category_id):
        category = get_object_or_404(self.get_queryset(), pk=product_category_id)
        data = request.data.copy()
        data["shop_id"] = shop_id
        serializer = self.serializer_class(category, data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, shop_id, product_category_id):
        category = get_object_or_404(self.get_queryset(), pk=product_category_id)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductCategoryView(ListCreateAPIView):
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return ProductCategory.objects.all()

class ProductCategoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductCategoryDetailSerializer

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCategorySerializer
        return ProductCategoryDetailSerializer

    def get_queryset(self):
        return ProductCategory.objects.all()

    def get_permissions(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsShopMember()]


# handles all package routes for a specific shop, including listing, creating, updating, and deleting packages
class ShopPackageView(APIView):
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self, shop_id):
        if not shop_id:
            raise ValidationError({"detail": "Shop ID is required"})
        return (
            Package.objects
            .filter(shop_id=shop_id)
            .select_related("shop")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=PackageItem.objects.select_related("product")
                )
            )
        )

    def get_permissions(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsShopMember()]

    def _parse_items(self, data):
        """
        Parse items from form-data (string) or leave as-is if already a list (JSON).
        Works safely with QueryDict.
        """

        # Convert QueryDict to normal dict to avoid nested list issues
        if hasattr(data, "dict"):
            data = data.dict()

        items = data.get("items")

        if items is not None:
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    raise ValidationError({"items": "Invalid JSON for items."})

            if not isinstance(items, list):
                raise ValidationError({"items": "Items must be a list."})

            data["items"] = items

        return data

    def get(self, request, shop_id, package_id=None):
        queryset = self.get_queryset(shop_id)
        if package_id is not None:
            package = get_object_or_404(queryset, pk=package_id)
            serializer = self.serializer_class(
                package,
                context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.serializer_class(
            queryset,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, shop_id):
        data = request.data.copy()
        data["shop_id"] = shop_id
        data = self._parse_items(data)
        serializer = self.serializer_class(
            data=data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, shop_id, package_id):
        package = get_object_or_404(self.get_queryset(shop_id), pk=package_id)
        data = request.data.copy()
        data["shop_id"] = shop_id
        data = self._parse_items(data)

        serializer = self.serializer_class(
            package,
            data=data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, shop_id, package_id):
        package = get_object_or_404(self.get_queryset(shop_id), pk=package_id)
        package.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, shop_id):
        total_products = Product.objects.filter(shop_id=shop_id).count()
        total_categories = ProductCategory.objects.filter(shop_id=shop_id).count()
        total_packages = Package.objects.filter(shop_id=shop_id).count()
        return Response({
            "products": total_products,
            "categories": total_categories,
            "packages": total_packages
        }, status=status.HTTP_200_OK)


