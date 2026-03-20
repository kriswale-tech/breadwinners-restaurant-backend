
from django.contrib import admin
from django.urls import path, include
from utils.views import catch_all
from django.conf.urls.static import static
from django.conf import settings

base_api_url = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path(base_api_url, include('accounts.urls')),
    path(base_api_url, include('shops.urls')),
    path(base_api_url, include('products.urls')),
    path(base_api_url, include('inventory.urls')),
    path(base_api_url, include('orders.urls')),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# catch-all LAST
urlpatterns += [
    path("<path:anything>/", catch_all),
]