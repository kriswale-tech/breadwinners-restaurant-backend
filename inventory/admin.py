from django.contrib import admin
from utils.admin import TimestampedAdminMixin

from .models import (
    Ingredient,
    IngredientInventory,
    ProductionBatch,
    ProductionBatchIngredient,
)


class IngredientInventoryInline(admin.StackedInline):
    model = IngredientInventory
    extra = 0
    can_delete = False


@admin.register(Ingredient)
class IngredientAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "shop", "unit")
    list_select_related = ("shop",)
    autocomplete_fields = ["shop"]
    search_fields = ("name", "shop__name", "unit")
    inlines = [IngredientInventoryInline]


@admin.register(IngredientInventory)
class IngredientInventoryAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "ingredient", "quantity")
    list_select_related = ("ingredient", "ingredient__shop")
    autocomplete_fields = ["ingredient"]
    search_fields = ("ingredient__name", "ingredient__shop__name")


class ProductionBatchIngredientInline(admin.TabularInline):
    model = ProductionBatchIngredient
    extra = 0
    autocomplete_fields = ["ingredient"]


@admin.register(ProductionBatch)
class ProductionBatchAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "shop", "product", "quantity_produced", "produced_by")
    list_select_related = ("shop", "product", "produced_by")
    autocomplete_fields = ["shop", "product", "produced_by"]
    search_fields = ("shop__name", "product__name", "produced_by__phone_number")
    inlines = [ProductionBatchIngredientInline]


@admin.register(ProductionBatchIngredient)
class ProductionBatchIngredientAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "production_batch", "ingredient", "quantity_used")
    list_select_related = ("production_batch", "ingredient")
    autocomplete_fields = ["production_batch", "ingredient"]
    search_fields = ("production_batch__product__name", "ingredient__name")