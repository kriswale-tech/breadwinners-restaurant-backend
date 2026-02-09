from django.shortcuts import render
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Product, ProductCategory
from .serializers import ProductSerializer, ProductCategorySerializer, ProductCategoryDetailSerializer
from rest_framework.viewsets import ModelViewSet


class ShopProductListView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(shop_id=self.kwargs["shop_id"])


class ProductView(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ProductCategoryView(ListCreateAPIView):
    serializer_class = ProductCategorySerializer

    def get_queryset(self):
        return ProductCategory.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]



class ProductCategoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductCategoryDetailSerializer

    def get_queryset(self):
        return ProductCategory.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]