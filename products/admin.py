from django.contrib import admin
from utils.admin import TimestampedAdminMixin

from .models import Package, PackageItem, Product, ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name", "description")


@admin.register(Product)
class ProductAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "category", "price")
    list_select_related = ("category",)
    autocomplete_fields = ["category"]
    search_fields = ("name", "description", "category__name")


class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Package)
class PackageAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inlines = [PackageItemInline]


@admin.register(PackageItem)
class PackageItemAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "package", "product", "quantity")
    list_select_related = ("package", "product")
    autocomplete_fields = ["package", "product"]
