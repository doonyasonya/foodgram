from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from .models import Subscription
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    AvatarSerializer,
    PasswordSerializer,
)

from core.paginations import UsersListPagination
from core.permissions import IsOwnerOrReadOnly
from recipes.serializers import SubscribeSerializer

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UsersListPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        elif self.action in (
            'me',
            'avatar',
            'set_password',
        ):
            self.permission_classes = [IsOwnerOrReadOnly]
        else:
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            avatar_url = serializer.save()
            return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            user = request.user
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = PasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if Subscription.objects.filter(
                user=request.user,
                author=author
            ).exists():
                return Response(
                    {'error': 'Уже подписан'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                user=request.user,
                author=author
            )
            serializer = SubscribeSerializer(
                subscription.author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=request.user,
                author=author
            )
            if not subscription:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                subscription[0].delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            subscription_user__user=request.user
        )
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscribeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscribeSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
