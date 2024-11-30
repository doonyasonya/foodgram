import csv
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    ModelMultipleChoiceFilter,
    ModelChoiceFilter,
    BooleanFilter
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
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
    ShoppingCart,
    FavoriteRecipe,
)
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeFavouriteSerializer,
    RecipeCreateSerializer,
    RecipeUpdateSerializer,
)

from core.paginations import RecipesListPagination
from core.permissions import IsAuthorOrReadOnly


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
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
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


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,
    )
    author = ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all(),
    )
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_in_shopping_cart',
            'is_favorited',
        ]

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = RecipesListPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeSerializer
        elif self.action == 'create':
            return RecipeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RecipeUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        short_link = self.generate_short_link(request, pk)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    def generate_short_link(self, request, recipe_id):
        base_url = request.build_absolute_uri('/')
        short_link = f'{base_url}recipes/{recipe_id}/'
        return short_link

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        author = request.user

        if request.method == 'POST':
            if author.favorited_by.filter(recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            FavoriteRecipe.objects.create(user=author, recipe=recipe)
            serializer = RecipeFavouriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite_item = author.favorited_by.filter(
                recipe=recipe
            ).first()
            if not favorite_item:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favorite_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        author = request.user

        if request.method == 'POST':
            if author.shopping_cart.filter(recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=author, recipe=recipe)
            serializer = RecipeFavouriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            shopping_cart_item = author.shopping_cart.filter(
                recipe=recipe
            ).first()
            if not shopping_cart_item:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(user=user)
        ingredients_data = {}
        for cart_item in shopping_cart_items:
            recipe = cart_item.recipe
            for recipe_ingredient in recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredient
                amount = recipe_ingredient.amount
                if ingredient in ingredients_data:
                    ingredients_data[ingredient] += amount
                else:
                    ingredients_data[ingredient] = amount
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        for ingredient, amount in ingredients_data.items():
            writer.writerow([
                ingredient.name,
                amount,
                ingredient.measurement_unit
            ])
        return response
