from rest_framework import serializers
from shops.models import Shop

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at', 'slug']