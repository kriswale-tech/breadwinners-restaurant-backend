from rest_framework import serializers
from .models import Ingredient, IngredientInventory, ProductionBatch, ProductionBatchIngredient
from django.db import transaction
from shops.models import Shop


class IngredientInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientInventory
        fields = ["quantity", "updated_at", "id"]


class IngredientSerializer(serializers.ModelSerializer):
    inventory_id = serializers.IntegerField(source='inventory.id', read_only=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, source='inventory.quantity')
    shop_id = serializers.IntegerField(required=False, source='shop.id')
    shop_name = serializers.CharField(source='shop.name', read_only=True)

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'unit', 'inventory_id', 'quantity', 'shop_id', 'shop_name']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate(self, attrs):
        # get shop_id from attrs
        shop_id = attrs.pop('shop')['id']
        quantity = attrs.pop('inventory')['quantity']
        if not shop_id:
            raise serializers.ValidationError("Shop is required")
        if not quantity:
            raise serializers.ValidationError("Quantity is required")

        attrs['shop_id'] = shop_id
        attrs['quantity'] = quantity
        return attrs

    def create(self, validated_data):
        quantity = validated_data.pop('quantity', None)
        shop_id = validated_data.pop('shop_id', None)

        # get shop
        shop = Shop.objects.get(id=shop_id)
        if not shop:
            raise serializers.ValidationError("Shop does not exist")

        # create ingredient
        ingredient = Ingredient.objects.create(shop=shop, **validated_data)

        # create ingredient inventory
    
        IngredientInventory.objects.create(ingredient=ingredient, quantity=quantity)
        return ingredient

    def update(self, instance, validated_data):
        quantity = validated_data.pop("quantity", None)
        shop_id = validated_data.pop("shop_id", None)

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise serializers.ValidationError("Shop does not exist")

        instance.shop = shop

        # update Ingredient fields too (PUT expects full update)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if quantity is not None:  # allows 0
            inventory, created = IngredientInventory.objects.get_or_create(
                ingredient=instance,
                defaults={"quantity": quantity},   # avoids NOT NULL on create
            )
            if not created:
                inventory.quantity = quantity
                inventory.save()

        return instance

class ProductionBatchIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = ProductionBatchIngredient
        fields = ['ingredient', 'quantity_used']


class ProductionBatchReadSerializer(serializers.ModelSerializer):
    ingredients_used = ProductionBatchIngredientSerializer(many=True)
    produced_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionBatch
        fields = ['shop', 'product', 'quantity_produced', 'produced_by', 'produced_by_name', 'ingredients_used']
    
    def get_produced_by_name(self, obj):
        if obj.produced_by:
            return obj.produced_by.get_full_name() or obj.produced_by.phone_number
        return None



''' 

Serializers for creating production batch ingredients (write only) 

'''
class ProductionBatchIngredientWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionBatchIngredient
        fields = ['ingredient', 'quantity_used']

class ProductionBatchWriteSerializer(serializers.ModelSerializer):
    ingredients = ProductionBatchIngredientWriteSerializer(many=True, source='ingredients_used')

    class Meta:
        model = ProductionBatch
        fields = ['shop', 'product', 'quantity_produced', 'produced_by', 'ingredients']
        extra_kwargs = {
            'produced_by': {'read_only': True},
        }

    def create(self, validated_data):
        with transaction.atomic():
            ingredients_used = validated_data.pop('ingredients_used', [])
            user = self.context['request'].user
            validated_data['produced_by'] = user

            # create production batch
            production_batch = ProductionBatch.objects.create(**validated_data)
            # create production batch ingredients
            for ingredient_data in ingredients_used:
               
                ingredient = Ingredient.objects.get(id=ingredient_data['ingredient'].id)

                if ingredient.inventory.quantity < ingredient_data['quantity_used']:
                    raise serializers.ValidationError({
                        'ingredient': f'Insufficient quantity of {ingredient.name} in inventory'
                    })
                else:
                    ingredient.inventory.quantity -= ingredient_data['quantity_used']
                    ingredient.inventory.save()

                ProductionBatchIngredient.objects.create(production_batch=production_batch, **ingredient_data)
            return production_batch