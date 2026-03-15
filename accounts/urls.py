from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from accounts.views import UserListCreate, UserDetails, SetupPasswordConfirmView, UserMe

app_name = 'accounts'

urlpatterns = [
    # Authentication (Login)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # logged in user
    path('user/', UserMe.as_view(), name='user_me'),

    # Setup password confirm
    path('auth/setup-password/', SetupPasswordConfirmView.as_view(), name='setup_password_confirm'),

    # Users
    path('users/', UserListCreate.as_view(), name='user_list_create'),
    path('users/<int:pk>/', UserDetails.as_view(), name='user_details'),

]