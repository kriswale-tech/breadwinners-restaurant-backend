from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import (
    PackageViewSet,
    ProductCategoryViewSet,
    ProductStatisticsView,
    ProductViewSet,
)

app_name = "products"

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"product-categories", ProductCategoryViewSet, basename="product-category")
router.register(r"packages", PackageViewSet, basename="package")

urlpatterns = [
    path("", include(router.urls)),
    path("product-statistics/", ProductStatisticsView.as_view(), name="product-statistics"),
]
