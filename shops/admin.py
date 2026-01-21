from django.contrib import admin
from utils.admin import TimestampedAdminMixin

from .models import Shop


@admin.register(Shop)
class ShopAdmin(TimestampedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name", "description")