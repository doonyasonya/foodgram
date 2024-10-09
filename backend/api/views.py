from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter
from .permissions import AuthorOrReadOnly
from .serializers import (
    FoodgramUserSerializer, FavoriteSerializer, FoodgramFollowSerializer,
    IngredientSerializer, RecipeCreateSerializer, RecipeSerializer,
    TagSerializer
)
from recipes.models import (
    Favourites, Ingredient, Recipe, RecipeIngredients, ShopCart, Tag
)
from users.models import FoodgramFollow, FoodgramUser


class FoodgramUserViewSet(UserViewSet):
    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer

    @action(['POST', 'DELETE'], detail=True)
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(FoodgramUser, id=kwargs.get('id'))
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Невозможно подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if FoodgramFollow.objects.filter(
                user=user,
                author=author
            ).exists():
                return Response(
                    {'errors': 'Уже есть подписка на автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = FoodgramFollow.objects.create(
                user=user, author=author
            )
            serializer = FoodgramFollowSerializer(
                follow, context={'request': request}
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        follow = FoodgramFollow.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Нет подписки на автора'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = FoodgramFollow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FoodgramFollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateSerializer

    def add_favorites(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = model.objects.create(user=request.user, recipe=recipe)
        serializer = FavoriteSerializer(
            instance, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_favorites(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if get_object_or_404(model, user=request.user, recipe=recipe).delete():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Этот рецепт еще не добавлен'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        ['POST', 'DELETE'], detail=True, permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, **kwargs):
        if request.method == 'POST':
            return self.add_favorites(Favourites, request, kwargs.get('pk'))
        return self.delete_favorites(Favourites, request, kwargs.get('pk'))

    @action(
        ['POST', 'DELETE'], detail=True, permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, **kwargs):
        if request.method == 'POST':
            return self.add_favorites(ShopCart, request, kwargs.get('pk'))
        return self.delete_favorites(ShopCart, request, kwargs.get('pk'))

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = (RecipeIngredients.objects.filter(
            recipe__shopping_recipe__user=request.user
        ).values(
            'ingredient'
        ).order_by(
            'ingredient__name'
        ).annotate(
            total_amount=Sum('amount')
        ).values_list(
            'ingredient__name', 'total_amount', 'ingredient__measurement_unit'
        ))
        shopping_cart = []
        for ingredient in ingredients:
            shopping_cart.append(
                f'{ingredient[0]} ({ingredient[2]}) - {ingredient[1]}\n'
            )
        response = HttpResponse(shopping_cart, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping.txt"'
        return response
