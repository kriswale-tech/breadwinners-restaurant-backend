from django.urls import path
from orders.views import (
    OrderView,
    OrderDetailView,
    OrderStatisticsView,
    InitializePaymentView,
    VerifyPaymentView,
    PaystackWebhookView,
    TrackOrderView,
)
app_name = 'orders'

urlpatterns = [
    path('shops/<int:shop_id>/orders/', OrderView.as_view(), name='order-list-create'),
    path('shops/<int:shop_id>/orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),

    # statistics
    path('shops/<int:shop_id>/orders/statistics/', OrderStatisticsView.as_view(), name='order-statistics'),

    # initialize payment
    path('shops/<int:shop_id>/orders/initialize-payment/', InitializePaymentView.as_view(), name='initialize-payment'),

    # verify payment
    path('shops/<int:shop_id>/orders/verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),

    # paystack webhook (Paystack sends POST requests here)
    path('paystack/webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),

    # track order
    path('orders/track/', TrackOrderView.as_view(), name='track-order'),
]