from django.db import models
from shops.models import Shop
from products.models import Product
from utils.models import TimeStampedSoftDeleteModel

class Order(TimeStampedSoftDeleteModel):
    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="orders")
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.customer_name} - {self.total_amount}"


class OrderItem(TimeStampedSoftDeleteModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price} = {self.total_price}"