from django.contrib import admin
from utils.admin import TimestampedAdminMixin

from .models import Product, ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name", "description")


@admin.register(Product)
class ProductAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "shop", "category", "price")
    list_select_related = ("shop", "category")
    autocomplete_fields = ["shop", "category"]
    search_fields = ("name", "description", "shop__name", "category__name")