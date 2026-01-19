from django.db import models
from shops.models import Shop
from utils.models import TimeStampedSoftDeleteModel

class Product(TimeStampedSoftDeleteModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
