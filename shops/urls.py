from django.urls import path, include
from rest_framework.routers import DefaultRouter
from shops.views import ShopViewSet

app_name = "shops"

router = DefaultRouter()
router.register(r'shops', ShopViewSet)

urlpatterns = [
    path('', include(router.urls)),
]