from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientView
from .views import ProductionBatchView
app_name = "inventory"

router = DefaultRouter()
router.register(r'ingredients', IngredientView, basename='ingredient')

urlpatterns = [
    # Add inventory routes here when views are defined
    path('', include(router.urls)),
    path('production-batches/', ProductionBatchView.as_view(), name='production-batches'),
    
]
