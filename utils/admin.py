from __future__ import annotations

from django.contrib import admin
from django.db import models


@admin.action(description="Hard delete selected (permanently remove from DB)")
def hard_delete_selected(modeladmin: admin.ModelAdmin, request, queryset):
    """
    Admin action to permanently delete rows from the DB.

    Works with your soft-delete models because they expose `hard_delete()`.
    Falls back to Django's delete if `hard_delete()` isn't present.
    """
    for obj in queryset:
        if hasattr(obj, "hard_delete"):
            obj.hard_delete()
        else:
            obj.delete()


@admin.action(description="Soft delete selected")
def soft_delete_selected(modeladmin: admin.ModelAdmin, request, queryset):
    """
    Admin action to soft-delete rows.

    For your soft-delete models this sets `is_deleted=True` (via overridden `delete()`).
    """
    for obj in queryset:
        obj.delete()


class SoftDeleteAdminMixin:
    """
    Drop-in admin mixin for models that have soft-delete fields/managers.

    - Shows deleted rows if the model exposes `all_objects`.
    - Adds `is_deleted` to list display + filters if present.
    - Adds a `hard_delete` admin action.
    """

    actions = [soft_delete_selected, hard_delete_selected]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If the model exposes an "all_objects" manager, show deleted rows too.
        all_objects = getattr(self.model, "all_objects", None)
        if all_objects is not None:
            return all_objects.get_queryset()
        return qs

    def get_list_display(self, request):
        base = list(super().get_list_display(request))
        if hasattr(self.model, "is_deleted") and "is_deleted" not in base:
            base.append("is_deleted")
        if hasattr(self.model, "deleted_at") and "deleted_at" not in base:
            base.append("deleted_at")
        return tuple(base)

    def get_list_filter(self, request):
        base = list(super().get_list_filter(request))
        if hasattr(self.model, "is_deleted") and "is_deleted" not in base:
            base.append("is_deleted")
        return tuple(base)


class TimestampedAdminMixin(SoftDeleteAdminMixin):
    """Convenience mixin for models that have created_at/updated_at."""

    def get_list_display(self, request):
        base = list(super().get_list_display(request))
        # Put timestamps at the end if present.
        if hasattr(self.model, "created_at") and "created_at" not in base:
            base.append("created_at")
        if hasattr(self.model, "updated_at") and "updated_at" not in base:
            base.append("updated_at")
        return tuple(base)

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        for f in ("created_at", "updated_at", "deleted_at"):
            if hasattr(self.model, f) and f not in base:
                base.append(f)
        return tuple(base)
