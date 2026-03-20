from rest_framework import serializers
from orders.models import Order
from shops.models import Shop
from products.models import Product, Package
from orders.models import OrderItem
import re
from django.db import transaction
from shops.serializers import ShopSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item can be either a product or a package (mutually exclusive)."""
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
        else:
            return None

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'package', 'package_name', 'quantity', 'unit_price', 'total_price', 'item_type']

    def validate(self, attrs):
        # Exactly one of product or package must be provided
        product = attrs.get('product')
        package = attrs.get('package')
        if product and package:
            raise serializers.ValidationError("Item cannot have both product and package.")
        if not product and not package:
            raise serializers.ValidationError("Item must have either product or package.")
        return attrs


class OrderListCreateSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    items = OrderItemSerializer(many=True, write_only=True)


    class Meta:
        model = Order
        fields = ['id', 'shop', 'shop_name', 'customer_name', 'customer_phone', 'status', 'total_amount', 'email', 'delivery_method', 'delivery_address', 'address_latitude', 'address_longitude', 'delivery_notes', 'order_number', 'created_at', 'updated_at', 'items']
        read_only_fields = ['order_number', 'created_at', 'updated_at', 'id', 'status', 'shop_name', 'shop']
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
            if not item.get("quantity"):
                raise serializers.ValidationError("Quantity is required")
            if not item.get("unit_price"):
                raise serializers.ValidationError("Unit price is required")
            if not item.get("total_price"):
                raise serializers.ValidationError("Total price is required")
        return value

    def validate(self, attrs):
        # check delivery method if delivery, then delivery_address, address_latitude, address_longitude are required
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
        # Use shop_id from view (URL) if provided;
        shop_id = validated_data.pop("shop_id", None)
        if shop_id is not None:
            try:
                shop = Shop.objects.get(id=shop_id)
            except Shop.DoesNotExist:
                raise serializers.ValidationError({"shop": "Shop does not exist"})
            validated_data["shop"] = shop
        else:
            raise serializers.ValidationError({"shop": "Shop id is required"})
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
        return order
    

class OrderDetailSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'shop', 'customer_name', 'customer_phone', 'status', 'total_amount', 'email', 'delivery_method', 'delivery_address', 'address_latitude', 'address_longitude', 'delivery_notes', 'order_number', 'created_at', 'updated_at', 'items']
        read_only_fields = ['order_number', 'created_at', 'updated_at', 'id', 'shop', 'items']

    def validate_customer_phone(self, value):
        if not value:
            raise serializers.ValidationError("Customer phone is required")
        if not re.match(r'^0\d{9}$', value):
            raise serializers.ValidationError("Invalid phone number. Must be 10 digits and of format 0XXXXXXXXX")
        return value
    def validate_items(self, value):
        if value is not None and len(value) == 0:
            raise serializers.ValidationError("Items must not be empty when provided")
        if value is not None:
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
                if not item.get("quantity"):
                    raise serializers.ValidationError("Quantity is required")
                if not item.get("unit_price"):
                    raise serializers.ValidationError("Unit price is required")
                if not item.get("total_price"):
                    raise serializers.ValidationError("Total price is required")
        return value

    def validate(self, attrs):
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
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            # Replace items if provided: delete existing, create new
            if items_data is not None:
                instance.items.all().delete()
                for item_data in items_data:
                    OrderItem.objects.create(order=instance, **item_data)
        return instance