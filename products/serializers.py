from rest_framework import serializers
from products.models import Product, ProductCategory, Package, PackageItem
from shops.models import Shop


class ProductCategorySerializer(serializers.ModelSerializer):
    # Flatten shop in responses: id + name.
    shop_id = serializers.IntegerField(required=False)
    shop_name = serializers.CharField(source='shop.name', read_only=True)

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'shop_id', 'shop_name', 'created_at', 'updated_at']

    def _resolve_shop(self, shop_id):
        # Centralized FK validation keeps create/update consistent.
        if not shop_id:
            raise serializers.ValidationError({"shop_id": "Shop is required"})
        try:
            return Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise serializers.ValidationError({"shop_id": "Shop does not exist"})

    def create(self, validated_data):
        shop_id = validated_data.pop('shop_id', None)
        shop = self._resolve_shop(shop_id)
        return ProductCategory.objects.create(shop=shop, **validated_data)

    def update(self, instance, validated_data):
        shop_id = validated_data.pop('shop_id', None)

        if shop_id is not None:
            instance.shop = self._resolve_shop(shop_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductSerializer(serializers.ModelSerializer):
    # Flatten relations in responses: ids + names.
    category_id = serializers.IntegerField(required=False, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    shop_id = serializers.IntegerField(required=False)
    shop_name = serializers.CharField(source='shop.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'image',
            'is_active',
            'category_id',
            'category_name',
            'shop_id',
            'shop_name',
            'created_at',
            'updated_at',
        ]

    def _resolve_shop(self, shop_id):
        # Shop is required for product write operations.
        if not shop_id:
            raise serializers.ValidationError({"shop_id": "Shop is required"})
        try:
            return Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise serializers.ValidationError({"shop_id": "Shop does not exist"})

    def _resolve_category(self, category_id):
        # Category is optional; return None when omitted/null.
        if not category_id:
            return None
        try:
            return ProductCategory.objects.get(id=category_id)
        except ProductCategory.DoesNotExist:
            raise serializers.ValidationError({"category_id": "Category does not exist"})

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        shop_id = validated_data.pop('shop_id', None)
        shop = self._resolve_shop(shop_id)

        # Create product with shop
        product = Product.objects.create(shop=shop, **validated_data)

        # Set category if provided
        category = self._resolve_category(category_id)
        if category:
            # Prevent cross-shop category assignment.
            if category.shop_id != shop.id:
                raise serializers.ValidationError({"category_id": "Category does not belong to this shop"})
            product.category = category
            product.save(update_fields=['category'])

        return product

    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        shop_id = validated_data.pop('shop_id', None)

        if shop_id is not None:
            instance.shop = self._resolve_shop(shop_id)

        if category_id is not None:
            category = self._resolve_category(category_id)
            # Category must belong to the product's effective shop.
            if category and category.shop_id != instance.shop_id:
                raise serializers.ValidationError({"category_id": "Category does not belong to this shop"})
            instance.category = category

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class ProductCategoryDetailSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'products', 'created_at', 'updated_at']


class PackageItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PackageItem
        fields = ['id', 'product', 'product_name', 'quantity']


class PackageSerializer(serializers.ModelSerializer):
    items = PackageItemSerializer(many=True, required=False)
    shop_id = serializers.IntegerField(required=False)

    class Meta:
        model = Package
        fields = ['id', 'name', 'description', 'price', 'image', 'is_active', 'shop_id', 'items']

    def _resolve_shop(self, shop_id):
        if not shop_id:
            raise serializers.ValidationError({"shop_id": "Shop is required"})
        try:
            return Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise serializers.ValidationError({"shop_id": "Shop does not exist"})

    def validate(self, attrs):
        items_data = attrs.get('items', [])

        # check if products item is not empty list
        if not items_data or len(items_data) == 0:
            raise serializers.ValidationError({"items": "At least one product is required"})

        # check if products are unique
        products = [item['product'].id for item in items_data]
        if len(products) != len(set(products)):
            raise serializers.ValidationError({"items": "Products must be unique"})

        # check if any of the products quantity is not positive
        for item in items_data:
            if item['quantity'] <= 0:
                raise serializers.ValidationError({"items": "Quantity must be positive"})
        
        # check if any of the products is not active
        for item in items_data:
            if not item['product'].is_active:
                raise serializers.ValidationError({"items": "Product must be active"})

        # shop_id from data (create) or instance (update)
        shop_id = attrs.get('shop_id') or (self.instance.shop_id if self.instance else None)
        if shop_id is not None:
            for item in items_data:
                if item['product'].shop_id != shop_id:
                    raise serializers.ValidationError({"items": "All products must belong to this shop"})

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        shop_id = validated_data.pop('shop_id', None)
        shop = self._resolve_shop(shop_id)

        package = Package.objects.create(shop=shop, **validated_data)
        for item_data in items_data:
            PackageItem.objects.create(package=package, **item_data)
        return package

    def update(self, instance, validated_data):
        validated_data.pop('shop_id', None)  # shop does not change on update
        items_data = validated_data.pop('items', None)

        # update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # update items if provided
        if items_data is not None:
            # simple strategy: upsert items, keep existing others
            for item_data in items_data:
                PackageItem.objects.update_or_create(
                    package=instance,
                    product=item_data['product'],
                    defaults={'quantity': item_data['quantity']},
                )
        return instance