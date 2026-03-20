from django.urls import path
from orders.views import OrderView, OrderDetailView, OrderStatisticsView
app_name = 'orders'

urlpatterns = [
    path('shops/<int:shop_id>/orders/', OrderView.as_view(), name='order-list-create'),
    path('shops/<int:shop_id>/orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),

    # statistics
    path('shops/<int:shop_id>/orders/statistics/', OrderStatisticsView.as_view(), name='order-statistics'),
]