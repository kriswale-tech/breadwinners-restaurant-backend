# accounts/managers.py (or in accounts/models.py)
from django.contrib.auth.base_user import BaseUserManager
from utils.models import SoftDeleteModel
from django.utils import timezone

class EmailUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

class SoftDeleteEmailUserManager(EmailUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteUserModel(SoftDeleteModel):
    """Soft delete model for User models with UserManager."""
    objects = SoftDeleteEmailUserManager()  # default manager (excludes deleted)
    all_objects = EmailUserManager()       # includes deleted

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

        update_fields = ["is_deleted", "deleted_at"]
        for field in ("updated_at", "is_active", "first_name", "last_name", "email", "password"):
            if hasattr(self, field):
                update_fields.append(field)

        self.save(update_fields=update_fields)

        
