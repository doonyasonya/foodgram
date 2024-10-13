from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning

from recipes.serializers import SubscribeSerializer
from utils.mixins import APIVersionMixin

from .models import Subscription
from .pagination import UserPagination
from .permissions import IsAuthenticatedUser, IsOwnerOrReadOnly
from .serializers import (
    AvatarSerializer,
    SetPasswordSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(APIVersionMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    http_method_names = ["get", "post", "put", "patch", "delete"]
    permission_classes = [IsAuthenticatedUser]
    versioning_class = AcceptHeaderVersioning

    def get_serializer_class(self):
        action_to_serializer = {
            "list": UserSerializer,
            "retrieve": UserDetailSerializer,
            "create": UserRegistrationSerializer,
            "set_password": SetPasswordSerializer,
            "avatar": UserDetailSerializer,
            "subscribe": SubscribeSerializer,
        }
        return action_to_serializer.get(self.action, UserSerializer)

    def get_permissions(self):
        if self.action in ["create", "get"]:
            self.permission_classes = [AllowAny]
        elif self.action in [
            "set_password",
            "avatar",
            "subscribe",
            "subscriptions",
            "me",
        ]:
            self.permission_classes = [IsOwnerOrReadOnly]
        elif self.action == "retrieve":
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_data = UserRegistrationSerializer(user).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        serializer = UserDetailSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request, *args, **kwargs):
        user = request.user
        if request.method in ["PUT", "PATCH"]:
            serializer = AvatarSerializer(data=request.data)
            if serializer.is_valid():
                avatar = serializer.validated_data["avatar"]
                user.avatar = avatar
                user.save()
                return Response({"avatar": user.avatar.url}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == "DELETE":
            if user.avatar and default_storage.exists(user.avatar.name):
                default_storage.delete(user.avatar.name)
                user.avatar = ""
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, id=pk)

        if user == author:
            return Response(
                {"errors": "You cannot subscribe to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if Subscription.objects.filter(user=user, subscribed_to=author).exists():
                return Response(
                    {"errors": "You are already subscribed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(user=user, subscribed_to=author)
            serializer = SubscribeSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            subscription = Subscription.objects.filter(
                user=user, subscribed_to=author
            ).first()
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"errors": "Subscription not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        queryset = User.objects.filter(users_subscribers__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(pages, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)