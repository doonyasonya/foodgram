import csv
from django.http import HttpResponse
from django.db.models import Count, Sum, F
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
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeFavouriteSerializer,
    RecipeCreateSerializer,
    SubscribeSerializer,
    UserSerializer,
    UserRegisterSerializer,
    AvatarSerializer,
    PasswordSerializer,
)

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    ShoppingCart,
    FavoriteRecipe,
)
from users.models import Subscription
from core.paginations import (
    RecipesListPagination,
    UsersListPagination,
)
from core.permissions import (
    IsAuthorOrReadOnly,
    IsOwnerOrReadOnly,
)


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
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
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

        ingredients_data = (
            ShoppingCart.objects.filter(user=user)
            .values(
                ingredient_name=F(
                    'recipe__recipeingredient__ingredient__name'
                ),
                measurement_unit=F(
                    'recipe__recipeingredient__ingredient__measurement_unit'
                ),
            )
            .annotate(total_amount=Sum('recipe__recipeingredient__amount'))
            .order_by('ingredient_name')
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])

        for ingredient in ingredients_data:
            writer.writerow([
                ingredient['ingredient_name'],
                ingredient['total_amount'],
                ingredient['measurement_unit'],
            ])

        return response


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
        serializer.is_valid(raise_exception=True)
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
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

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
            if request.user.subscription_user.filter(
                author=author
            ).exists():
                return Response(
                    {'error': 'Уже подписан'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            author = User.objects.annotate(
                recipes_count=Count('recipes')
            ).get(pk=author.pk)
            serializer = SubscribeSerializer(
                author,
                context={'request': request}
            )
            serializer.validate({})

            subscription = Subscription.objects.create(
                user=request.user,
                author=author
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = request.user.subscription_user.filter(
                author=author
            )
            if not subscription:
                return Response(status=status.HTTP_400_BAD_REQUEST)
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
            subscription_author__user=request.user
        ).annotate(recipes_count=Count('recipes'))
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
