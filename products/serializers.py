from rest_framework import serializers
from products.models import Product, ProductCategory
from shops.serializers import ShopSerializer
from shops.models import Shop


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True, allow_null=True)
    shop = ShopSerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, allow_null=True)
    shop_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'shop', 'category_id', 'shop_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        shop_id = validated_data.pop('shop_id', None)
         # Validate shop exists BEFORE creating product
        if shop_id:
            try:
                shop = Shop.objects.get(id=shop_id)
            except Shop.DoesNotExist:
                raise serializers.ValidationError({"shop_id": "Shop does not exist"})
        else:
            raise serializers.ValidationError({"shop_id": "Shop is required"})
        
        # Create product WITH shop
        product = Product.objects.create(shop=shop, **validated_data)
        
        # Set category if provided
        if category_id:
            try:
                product.category = ProductCategory.objects.get(id=category_id)
                product.save()
            except ProductCategory.DoesNotExist:
                raise serializers.ValidationError({"category_id": "Category does not exist"})
        
        return product



class ProductCategoryDetailSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'products', 'created_at', 'updated_at']