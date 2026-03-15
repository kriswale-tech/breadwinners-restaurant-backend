from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from accounts.models import User
from accounts.serializers import UserListCreateSerializer, UserDetailsSerializer, UserDetailsUpdateSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import SetupPasswordConfirmSerializer

# Create your views here.

class UserListCreate(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all().filter(is_superuser=False).select_related('profile')
    serializer_class = UserListCreateSerializer


class UserDetails(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserDetailsSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserDetailsUpdateSerializer
        return UserDetailsSerializer


class UserMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailsSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SetupPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SetupPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password setup successful'}, status=status.HTTP_200_OK)