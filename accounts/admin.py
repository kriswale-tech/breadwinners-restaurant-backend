from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from utils.admin import SoftDeleteAdminMixin

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    can_delete = False
    fields = ("role", "shop", "avatar", "address", "bio")


@admin.register(User)
class UserAdmin(SoftDeleteAdminMixin, DjangoUserAdmin):
    ordering = ("phone_number",)
    list_display = (
        "id",
        "phone_number",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("phone_number", "first_name", "last_name")
    inlines = [ProfileInline]

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Soft delete"), {"fields": ("is_deleted", "deleted_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number", "password1", "password2", "first_name", "last_name"),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "user", "role", "get_phone_number", "address")
    list_select_related = ("user",)
    autocomplete_fields = ["user"]
    list_filter = ("role", "is_deleted")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name", "address")
    fieldsets = (
        (None, {"fields": ("user", "role")}),
        (_("Contact info"), {"fields": ("address",)}),
        (_("Additional info"), {"fields": ("avatar", "bio")}),
        (_("Soft delete"), {"fields": ("is_deleted", "deleted_at")}),
    )

    def get_phone_number(self, obj):
        return obj.user.phone_number
    get_phone_number.short_description = "Phone number"
    get_phone_number.admin_order_field = "user__phone_number"