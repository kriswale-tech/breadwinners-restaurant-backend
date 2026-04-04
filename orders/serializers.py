from decimal import Decimal

from rest_framework import serializers
from orders.models import Order, OrderItem
from products.models import Product, Package
from shops.models import Shop
from shops.serializers import ShopSerializer
import re
from django.db import transaction


class OrderItemWriteSerializer(serializers.Serializer):
    """
    Write-only: client sends product/package + quantity only.
    unit_price and total_price are derived server-side from Product.price or Package.price.
    """
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    package = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product = attrs.get('product')
        package = attrs.get('package')
        if product and package:
            raise serializers.ValidationError("Item cannot have both product and package.")
        if not product and not package:
            raise serializers.ValidationError("Item must have either product or package.")
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    """Read-only: includes server-stored unit_price, total_price."""
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    package = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(), required=False, allow_null=True
    )
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)
    package_name = serializers.CharField(source='package.name', read_only=True, allow_null=True)
    item_type = serializers.SerializerMethodField(read_only=True)

    def get_item_type(self, obj):
        if obj.product:
            return "product"
        elif obj.package:
            return "package"
        return None

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'package', 'package_name', 'quantity', 'unit_price', 'total_price', 'item_type']


class OrderListCreateSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    # Client sends product/package + quantity only; prices derived server-side
    items = OrderItemWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'shop', 'shop_name', 'customer_name', 'customer_phone', 'status', 'total_amount', 'email', 'delivery_method', 'delivery_address', 'address_latitude', 'address_longitude', 'delivery_notes', 'order_number', 'created_at', 'updated_at', 'items', 'payment_status']
        read_only_fields = ['order_number', 'created_at', 'updated_at', 'id', 'status', 'shop_name', 'shop', 'total_amount', 'payment_status']
        extra_kwargs = {
            'delivery_address': {'write_only': True},
            'address_latitude': {'write_only': True},
            'address_longitude': {'write_only': True},
            'delivery_notes': {'write_only': True},
            'items': {'write_only': True},
            'email': {'write_only': True},
        }

    def validate_customer_phone(self, value):
        if not value:
            raise serializers.ValidationError("Customer phone is required")
        if not re.match(r'^0\d{9}$', value):
            raise serializers.ValidationError("Invalid phone number. Must be 10 digits and of format 0XXXXXXXXX")
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Items are required")
        if not isinstance(value, list):
            raise serializers.ValidationError("Items must be a list")
        if len(value) == 0:
            raise serializers.ValidationError("Items must not be empty")
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each item must be a dictionary")
            # Each item must have either product or package (not both, not neither)
            has_product = item.get("product") is not None
            has_package = item.get("package") is not None
            if has_product and has_package:
                raise serializers.ValidationError("Item cannot have both product and package.")
            if not has_product and not has_package:
                raise serializers.ValidationError("Item must have either product or package.")
            if not item.get("quantity") or item.get("quantity") < 1:
                raise serializers.ValidationError("Quantity is required and must be at least 1")
        return value

    def validate(self, attrs):
        # Delivery method: if delivery, require address and coordinates
        delivery_method = attrs.get("delivery_method")

        delivery_address = attrs.get("delivery_address")
        latitude = attrs.get("address_latitude")
        longitude = attrs.get("address_longitude")

        if delivery_method == "delivery":
            if not delivery_address:
                raise serializers.ValidationError({
                    "delivery_address": "Delivery address is required for delivery orders"
                })

            if latitude is None or longitude is None:
                raise serializers.ValidationError({
                    "coordinates": "Latitude and longitude are required for delivery orders"
                })

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        shop_id = validated_data.pop("shop_id", None)
        if shop_id is None:
            raise serializers.ValidationError({"shop": "Shop id is required"})
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise serializers.ValidationError({"shop": "Shop does not exist"})
        validated_data["shop"] = shop

        # total_amount derived from items; create with 0 first, then update
        validated_data.pop("total_amount", None)
        validated_data["total_amount"] = Decimal("0")

        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            order_total = Decimal("0")
            for item_data in items_data:
                product = item_data.get("product")
                package = item_data.get("package")
                quantity = item_data["quantity"]

                # Derive unit_price from product or package (never trust client)
                if product:
                    if not product.is_active:
                        raise serializers.ValidationError({"items": f"Product {product.name} is not active"})
                    unit_price = product.price
                else:
                    if not package.is_active:
                        raise serializers.ValidationError({"items": f"Package {package.name} is not active"})
                    unit_price = package.price

                total_price = unit_price * quantity
                order_total += total_price
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    package=package,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )
            order.total_amount = order_total
            order.save(update_fields=["total_amount"])
        return order
    

class OrderDetailSerializer(serializers.ModelSerializer):
    """Read-only for retrieve (GET)."""
    shop = ShopSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'shop', 'customer_name', 'customer_phone', 'status', 'total_amount', 'email', 'delivery_method', 'delivery_address', 'address_latitude', 'address_longitude', 'delivery_notes', 'order_number', 'created_at', 'updated_at', 'items', 'payment_status']
        read_only_fields = ['order_number', 'created_at', 'updated_at', 'id', 'shop', 'items', 'payment_status']


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer: only status is writable.
    Prevents changes to customer info, items, delivery, etc. after order creation
    (e.g. after payment is made).
    """
    status = serializers.ChoiceField(choices=Order.StatusChoices.choices)
    shop = ShopSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'shop', 'customer_name', 'customer_phone', 'status', 'total_amount', 'email', 'delivery_method', 'delivery_address', 'address_latitude', 'address_longitude', 'delivery_notes', 'order_number', 'created_at', 'updated_at', 'items', 'payment_status']
        read_only_fields = ['id', 'shop', 'customer_name', 'customer_phone', 'total_amount', 'email', 'delivery_method', 'delivery_address', 'address_latitude', 'address_longitude', 'delivery_notes', 'order_number', 'created_at', 'updated_at', 'items', 'payment_status']


class TrackOrderSerializer(serializers.Serializer):
    order_number = serializers.CharField(required=True)
    customer_phone = serializers.CharField(required=True)

    def validate_customer_phone(self, value):
        if not re.match(r'^0\d{9}$', value):
            raise serializers.ValidationError("Invalid phone number. Must be 10 digits and of format 0XXXXXXXXX")
        return value

    def validate(self, attrs):
        order_number = attrs.get("order_number")
        customer_phone = attrs.get("customer_phone")
        if not order_number:
            raise serializers.ValidationError("Order number is required")
        if not customer_phone:
            raise serializers.ValidationError("Phone number is required")
        return attrs