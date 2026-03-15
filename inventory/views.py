from django.shortcuts import get_object_or_404, render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .serializers import IngredientSerializer
from .models import Ingredient, ProductionBatch
from rest_framework.views import APIView
from .serializers import ProductionBatchWriteSerializer, ProductionBatchReadSerializer
from rest_framework.response import Response
from rest_framework import status
from permissions.shop_permissions import IsShopMember
from rest_framework.exceptions import ValidationError
# Create your views here.
class IngredientView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")

        if not shop_id:
            raise ValidationError({"detail": "Shop ID is required"})

        return (
            Ingredient.objects
            .filter(shop_id=shop_id)
            .select_related("inventory", "shop")
            .order_by("name")
        )

    def get(self, request, shop_id):
        ingredients = self.get_queryset()
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, shop_id):
        data = request.data.copy()
        data['shop_id'] = shop_id
        serializer = IngredientSerializer(data=data)
        print(serializer.initial_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, shop_id, ingredient_id):
        data = request.data.copy()
        data['shop_id'] = shop_id
        ingredient = get_object_or_404(self.get_queryset(), pk=ingredient_id)
        serializer = IngredientSerializer(ingredient, data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, shop_id, ingredient_id):
        ingredient = get_object_or_404(self.get_queryset(), pk=ingredient_id)
        ingredient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ProductionBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        production_batches = ProductionBatch.objects.all()
        serializer = ProductionBatchReadSerializer(production_batches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductionBatchWriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = {
                'message': 'Production batch created successfully',
                'production_batch': ProductionBatchReadSerializer(serializer.instance).data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)