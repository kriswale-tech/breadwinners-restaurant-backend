from django.db import models
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

class TimeStampedSoftDeleteModel(TimeStampedModel, SoftDeleteGenericModel):
    """Combines TimeStampedModel and SoftDeleteGenericModel for convenience."""
    class Meta:
        abstract = True
