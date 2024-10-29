from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from .serializers import UserSerializer, UserRegisterSerializer
from core.paginations import UsersListPagination

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UsersListPagination

    def get_serializer_class(self):
        return {
            'create': UserRegisterSerializer,
        }.get(self.action, UserSerializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()
        data = UserRegisterSerializer(user).data
        return Response(data, status=status.HTTP_201_CREATED)
