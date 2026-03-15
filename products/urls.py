from django.urls import path, include
from products.views import (
    ShopProductsView,
    ShopProductCategoriesView,
    ProductView,
    ProductCategoryView,
    ProductCategoryDetailView,
    ShopPackageView,
    ProductStatisticsView,
)
from rest_framework.routers import DefaultRouter
app_name = "products"

router = DefaultRouter()
router.register(r'products', ProductView, basename='product')

urlpatterns = [
    # shop product routes
    path('shops/<int:shop_id>/products/', ShopProductsView.as_view(), name='shop-product-list-create'),
    path('shops/<int:shop_id>/products/<int:product_id>/', ShopProductsView.as_view(), name='shop-product-detail'),

    #shop category routes
    path('shops/<int:shop_id>/product-categories/', ShopProductCategoriesView.as_view(), name='shop-product-category-list-create'),
    path('shops/<int:shop_id>/product-categories/<int:product_category_id>/', ShopProductCategoriesView.as_view(), name='shop-product-category-detail'),

    # shop package routes
    path('shops/<int:shop_id>/packages/', ShopPackageView.as_view(), name='shop-package-list-create'),
    path('shops/<int:shop_id>/packages/<int:package_id>/', ShopPackageView.as_view(), name='shop-package-detail'),

    # product routes
    path('', include(router.urls)),


    # product category routes
    path('product-categories/', ProductCategoryView.as_view(), name='product-category-list'),
    path('product-categories/<int:pk>/', ProductCategoryDetailView.as_view(), name='product-category-detail'),

    # Statistics route
    path('shops/<int:shop_id>/statistics/', ProductStatisticsView.as_view(), name='shop-statistics'),
]
