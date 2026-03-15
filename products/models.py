from django.db import models
from shops.models import Shop
from utils.models import TimeStampedSoftDeleteModel



class ProductCategory(TimeStampedSoftDeleteModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="product_categories")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(TimeStampedSoftDeleteModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Package(TimeStampedSoftDeleteModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PackageItem(TimeStampedSoftDeleteModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="package_items")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.package.name} - {self.product.name} - {self.quantity}"