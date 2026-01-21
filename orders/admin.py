from django.contrib import admin
from utils.admin import TimestampedAdminMixin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Order)
class OrderAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "shop", "customer_name", "customer_phone", "status", "total_amount")
    list_select_related = ("shop",)
    autocomplete_fields = ["shop"]
    search_fields = ("customer_name", "customer_phone", "shop__name")
    list_filter = ("status",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "unit_price", "total_price")
    list_select_related = ("order", "product", "order__shop")
    autocomplete_fields = ["order", "product"]
    search_fields = ("order__customer_name", "order__shop__name", "product__name")