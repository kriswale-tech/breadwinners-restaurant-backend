from django.urls import path, include
from products.views import ShopProductListView, ProductView, ProductCategoryView, ProductCategoryDetailView
from rest_framework.routers import DefaultRouter
app_name = "products"

router = DefaultRouter()
router.register(r'products', ProductView, basename='product')

urlpatterns = [
    # Add product routes here when views are defined
    path('shops/<int:shop_id>/products/', ShopProductListView.as_view(), name='shop-product-list'),
    path('', include(router.urls)),


    # product category routes
    path('product-categories/', ProductCategoryView.as_view(), name='product-category-list'),
    path('product-categories/<int:pk>/', ProductCategoryDetailView.as_view(), name='product-category-detail'),
]
