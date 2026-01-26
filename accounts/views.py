from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from accounts.models import User
from accounts.serializers import UserListCreateSerializer, UserDetailsSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class UserListCreate(ListCreateAPIView):
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserListCreateSerializer
    permission_classes = [IsAuthenticated]


class UserDetails(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserDetailsSerializer
    permission_classes = [IsAuthenticated]

