# accounts/managers.py (or in accounts/models.py)
from django.contrib.auth.base_user import BaseUserManager
from utils.models import SoftDeleteModel
from django.utils import timezone

class EmailUserManager(BaseUserManager):
    """
    Base manager for the custom User model.

    Despite the name (kept for migration compatibility), this manager now
    treats `phone_number` as the primary identifier, matching USERNAME_FIELD.
    """

    use_in_migrations = True

    def create_user(self, phone_number, password=None, **extra_fields):
        """
        Create and save a regular user with the given phone number and password.
        """
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """
        Create and save a superuser with the given phone number and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)

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
            if hasattr(self, "phone_number") and getattr(self, "phone_number"):
                # Use a non-phone sentinel that still satisfies uniqueness.
                self.phone_number = f"deleted+{self.pk}"

        update_fields = ["is_deleted", "deleted_at"]
        for field in ("updated_at", "is_active", "first_name", "last_name", "phone_number", "password"):
            if hasattr(self, field):
                update_fields.append(field)

        self.save(update_fields=update_fields)

        
