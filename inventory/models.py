from django.db import models
from shops.models import Shop
from utils.models import TimeStampedSoftDeleteModel
from products.models import Product
from django.conf import settings

class Ingredient(TimeStampedSoftDeleteModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="ingredients")
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)  # kg, g, L, ml, pcs
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class IngredientInventory(TimeStampedSoftDeleteModel):
    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity}{self.ingredient.unit}"


class ProductionBatch(TimeStampedSoftDeleteModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="production_batches")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="production_batches")
    quantity_produced = models.PositiveIntegerField()
    produced_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="production_batches")

    def __str__(self):
        return f"{self.product.name} x {self.quantity_produced}"


class ProductionBatchIngredient(TimeStampedSoftDeleteModel):
    production_batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name="ingredients_used"
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.ingredient.name} - {self.quantity_used}{self.ingredient.unit}"