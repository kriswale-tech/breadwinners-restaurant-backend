
from django.contrib import admin
from django.urls import path, include

base_api_url = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path(base_api_url, include('accounts.urls')),
    path(base_api_url, include('shops.urls')),
    path(base_api_url, include('products.urls')),
    path(base_api_url, include('inventory.urls')),
    path(base_api_url, include('orders.urls')),
]
