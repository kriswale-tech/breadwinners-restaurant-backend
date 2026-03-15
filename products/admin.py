from django.contrib import admin
from utils.admin import TimestampedAdminMixin

from .models import Product, ProductCategory, Package, PackageItem


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

class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 0
    autocomplete_fields = ["product"]
    
@admin.register(Package)
class PackageAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "shop", "price", "is_active")
    list_select_related = ("shop",)
    list_filter = ("is_active", "shop")
    autocomplete_fields = ["shop"]
    search_fields = ("name", "description", "shop__name")
    inlines = [PackageItemInline]


@admin.register(PackageItem)
class PackageItemAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "package", "product", "quantity")
    list_select_related = ("package", "product")
    autocomplete_fields = ["package", "product"]