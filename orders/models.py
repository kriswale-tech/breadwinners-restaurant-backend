from django.db import models
from shops.models import Shop
from products.models import Product, Package
from utils.models import TimeStampedSoftDeleteModel
from django.utils import timezone
from django.db import transaction

class Order(TimeStampedSoftDeleteModel):
    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending" # when the order is created, not yet confirmed by the staff
        CONFIRMED = "confirmed", "Confirmed" # when the staff confirms the order
        CANCELLED = "cancelled", "Cancelled" # when the staff cancels the order
        DELIVERED = "delivered", "Delivered" # when the order is delivered to the customer
        DONE = "done", "Done" # when the order is completed

    class DeliveryMethodChoices(models.TextChoices):
        DELIVERY = "delivery", "Delivery"
        PICKUP = "pickup", "Pickup"

    class PaymentStatusChoices(models.TextChoices):
        PAID = "paid", "Paid"
        UNPAID = "unpaid", "Unpaid"


    order_number = models.CharField(max_length=20, unique=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="orders")
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField(blank=True, null=True)
    delivery_method = models.CharField(max_length=20, choices=DeliveryMethodChoices.choices, default=DeliveryMethodChoices.PICKUP)
    delivery_address = models.TextField(blank=True, null=True)
    address_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    address_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    delivery_notes = models.TextField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.UNPAID)

    def __str__(self):
        return f"{self.customer_name} - {self.total_amount}"

    def save(self, *args, **kwargs):

        if not self.order_number:
            with transaction.atomic():
                now = timezone.now()
                month_day = now.strftime("%m%d")

                today_orders = Order.objects.filter(
                    shop=self.shop,
                    created_at__date=now.date()
                ).count()

                sequence = today_orders + 1

                self.order_number = f"ORD{self.shop.id}{month_day}{sequence:04d}"
        super().save(*args, **kwargs)


class OrderItem(TimeStampedSoftDeleteModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items", null=True, blank=True)
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name="order_items", null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        if self.product:
            return f"{self.product.name} - {self.quantity} x {self.unit_price} = {self.total_price}"
        elif self.package:
            return f"{self.package.name} - {self.quantity} x {self.unit_price} = {self.total_price}"
        else:
            return f"Unknown - {self.quantity} x {self.unit_price} = {self.total_price}"



class PendingPayment(TimeStampedSoftDeleteModel):

    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    reference = models.CharField(max_length=255, unique=True) # payment reference
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField()

    # store cart + metadata
    order_data = models.JSONField()
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="pending_payments")

    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    order = models.ForeignKey(Order, on_delete=models.SET_NULL, related_name="pending_payments", null=True, blank=True)