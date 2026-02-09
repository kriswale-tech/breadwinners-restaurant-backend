from rest_framework import serializers
from shops.models import Shop

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']