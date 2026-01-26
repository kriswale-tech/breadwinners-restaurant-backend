from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from utils.admin import SoftDeleteAdminMixin

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    can_delete = False
    fields = ("role", "phone_number", "avatar", "address", "bio")


@admin.register(User)
class UserAdmin(SoftDeleteAdminMixin, DjangoUserAdmin):
    """
    Custom user admin for email-based auth (no username field).
    """

    ordering = ("email",)
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    inlines = [ProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
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
                "fields": ("email", "password1", "password2", "first_name", "last_name"),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "user", "role", "phone_number", "address")
    list_select_related = ("user",)
    autocomplete_fields = ["user"]
    list_filter = ("role", "is_deleted")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone_number", "address")
    fieldsets = (
        (None, {"fields": ("user", "role")}),
        (_("Contact info"), {"fields": ("phone_number", "address")}),
        (_("Additional info"), {"fields": ("avatar", "bio")}),
        (_("Soft delete"), {"fields": ("is_deleted", "deleted_at")}),
    )