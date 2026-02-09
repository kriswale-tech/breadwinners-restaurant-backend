from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .serializers import IngredientSerializer
from .models import Ingredient, ProductionBatch
from rest_framework.views import APIView
from .serializers import ProductionBatchWriteSerializer, ProductionBatchReadSerializer
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class IngredientView(ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ingredient.objects.all()


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