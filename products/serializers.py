from rest_framework import serializers
from products.models import Product, ProductCategory, Package, PackageItem


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    category_name = serializers.CharField(source="category.name", read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "image",
            "is_active",
            "category_id",
            "category_name",
            "created_at",
            "updated_at",
        ]

    def _resolve_category(self, category_id):
        if not category_id:
            return None
        try:
            return ProductCategory.objects.get(id=category_id)
        except ProductCategory.DoesNotExist:
            raise serializers.ValidationError({"category_id": "Category does not exist"})

    def create(self, validated_data):
        category_id = validated_data.pop("category_id", None)
        product = Product.objects.create(**validated_data)
        category = self._resolve_category(category_id)
        if category:
            product.category = category
            product.save(update_fields=["category"])
        return product

    def update(self, instance, validated_data):
        category_id = validated_data.pop("category_id", None)
        if "category_id" in self.initial_data:
            instance.category = self._resolve_category(category_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductCategoryDetailSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "description", "products", "created_at", "updated_at"]


class PackageItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PackageItem
        fields = ["id", "product", "product_name", "quantity"]


class PackageSerializer(serializers.ModelSerializer):
    items = PackageItemSerializer(many=True, required=False)

    class Meta:
        model = Package
        fields = ["id", "name", "description", "price", "image", "is_active", "items"]

    def validate(self, attrs):
        if "items" not in attrs:
            return attrs
        items_data = attrs.get("items") or []

        if not items_data or len(items_data) == 0:
            raise serializers.ValidationError({"items": "At least one product is required"})

        products = [item["product"].id for item in items_data]
        if len(products) != len(set(products)):
            raise serializers.ValidationError({"items": "Products must be unique"})

        for item in items_data:
            if item["quantity"] <= 0:
                raise serializers.ValidationError({"items": "Quantity must be positive"})

        for item in items_data:
            if not item["product"].is_active:
                raise serializers.ValidationError({"items": "Product must be active"})

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        package = Package.objects.create(**validated_data)
        for item_data in items_data:
            PackageItem.objects.create(package=package, **item_data)
        return package

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            # Replace strategy: incoming list is the source of truth.
            instance.items.all().delete()
            for item_data in items_data:
                PackageItem.objects.create(
                    package=instance,
                    product=item_data["product"],
                    quantity=item_data["quantity"],
                )
        return instance
