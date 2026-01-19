from django.db import models
from django.contrib.auth.models import UserManager
from django.utils import timezone

# Create your models here.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteUserManager(UserManager):
    """UserManager that excludes soft-deleted users by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteModel(models.Model):
    """Base soft delete model with fields and delete methods (no managers)."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete:
        - Marks the row as deleted instead of removing it from the DB.
        - Keeps relationships intact (FKs still point to this row).
        NOTE: bulk QuerySet.delete() bypasses this method; call delete() on instances.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        
        update_fields = ["is_deleted", "deleted_at"]
        if hasattr(self, "updated_at"):
            update_fields.append("updated_at")

        self.save(update_fields=update_fields)

    def hard_delete(self):
        super(SoftDeleteModel, self).delete()

class SoftDeleteGenericModel(SoftDeleteModel):
    """Generic soft delete model with standard Manager."""
    objects = SoftDeleteManager()     # default manager (excludes deleted)
    all_objects = models.Manager()    # includes deleted

    class Meta:
        abstract = True

class SoftDeleteUserModel(SoftDeleteModel):
    """Soft delete model for User models with UserManager."""
    objects = SoftDeleteUserManager()  # default manager (excludes deleted)
    all_objects = UserManager()       # includes deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Option A: soft delete + anonymize user.

        Goal:
        - Keep the user row for history/audit and FK integrity.
        - Remove personal identifiers so the original email/username can be reused.

        Restore implications:
        - You can flip is_deleted/is_active back, but you cannot recover the old
          email/name/username because we overwrite them here.
        - A "restored" user should verify a new email / pick a new username.
        """
        now = timezone.now()

        # Soft delete flags
        self.is_deleted = True
        self.deleted_at = now

        # Prevent login (most auth backends check `is_active`).
        if hasattr(self, "is_active"):
            self.is_active = False

        # Remove human-identifying profile fields.
        if hasattr(self, "first_name"):
            self.first_name = ""
        if hasattr(self, "last_name"):
            self.last_name = ""

        # Make credentials unusable (so password auth can't succeed).
        if hasattr(self, "set_unusable_password"):
            self.set_unusable_password()

        # Anonymize identifiers to free them for reuse.
        # PK-based values are unique and idempotent.
        if getattr(self, "pk", None) is not None:
            if hasattr(self, "email"):
                self.email = f"deleted+{self.pk}@example.invalid"
            if hasattr(self, "username"):
                self.username = f"deleted_{self.pk}"

        update_fields = ["is_deleted", "deleted_at"]
        for field in ("updated_at", "is_active", "first_name", "last_name", "email", "username", "password"):
            if hasattr(self, field):
                update_fields.append(field)

        self.save(update_fields=update_fields)

class TimeStampedSoftDeleteModel(TimeStampedModel, SoftDeleteGenericModel):
    """Combines TimeStampedModel and SoftDeleteGenericModel for convenience."""
    class Meta:
        abstract = True
