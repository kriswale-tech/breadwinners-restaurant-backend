from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientView
from .views import ProductionBatchView
app_name = "inventory"

# router = DefaultRouter()
# router.register(r'ingredients', IngredientView, basename='ingredient')

urlpatterns = [
    # Add inventory routes here when views are defined
    path('shops/<int:shop_id>/ingredients/', IngredientView.as_view(), name='ingredients-list-create'),
    path('shops/<int:shop_id>/ingredients/<int:ingredient_id>/', IngredientView.as_view(), name='ingredients-detail'),

# Production Batches
    path('shops/<int:shop_id>/production-batches/', ProductionBatchView.as_view(), name='production-batches'),
    path('shops/<int:shop_id>/production-batches/<int:production_batch_id>/', ProductionBatchView.as_view(), name='production-batch-detail'),
    
]
