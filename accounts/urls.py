from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from accounts.views import UserListCreate, UserDetails

app_name = 'accounts'

urlpatterns = [
    # Authentication (Login)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Users
    path('users/', UserListCreate.as_view(), name='user_list_create'),
    path('users/<int:pk>/', UserDetails.as_view(), name='user_details'),
]