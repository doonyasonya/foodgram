from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import FilterSet, CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)
from rest_framework.response import Response

from .models import (
    Tag,
    Ingredient,
    Recipe,
)
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeFavouriteSerializer,
    RecipeCreateSerializer,
    RecipeUpdateSerializer,
)

# from core.paginations import UsersListPagination


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            tag = get_object_or_404(self.queryset, pk=kwargs['pk'])
            serializer = self.get_serializer(tag)
            return Response(serializer.data)
        tags = self.queryset.all()
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            ingredient = get_object_or_404(self.queryset, pk=kwargs['pk'])
            serializer = self.get_serializer(ingredient)
            return Response(serializer.data)
        tags = self.queryset.all()
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeSerializer
        elif self.action == 'create':
            return RecipeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RecipeUpdateSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        methods=['post', 'delete',],
        permission_classes=[IsAuthenticated,],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = RecipeFavouriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete',],
        permission_classes=[IsAuthenticated,],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = RecipeFavouriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get',],
        permission_classes=[IsAuthenticated,],
    )
    def download_shopping_cart(self, request):
        pass
