from django.db import models, transaction
from utils.models import TimeStampedSoftDeleteModel


class ProductCategory(TimeStampedSoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TimeStampedSoftDeleteModel):
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """
        Soft-delete package item links first so deleted products stop appearing in package edits.
        """
        with transaction.atomic():
            self.package_items.all().delete()
            return super().delete(using=using, keep_parents=keep_parents)


class Package(TimeStampedSoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="packages/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PackageItem(TimeStampedSoftDeleteModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="package_items")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.package.name} - {self.product.name} - {self.quantity}"
