import base64

from djoser.serializers import UserCreateSerializer
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Tag,
    RecipeIngredients,
    Recipe,
    ShopCart,
    Favourites,
)
from users.models import (FoodgramUser, FoodgramFollow)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.followers.filter(author=author).exists()
        return False


class FoodgramUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = FoodgramUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class FollowRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта подписки."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FoodgramFollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписки пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return (
                FoodgramFollow.objects.filter(user=user, author=obj).exists()
            )
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if limit:
            recipes = recipes[:int(limit)]
        return FollowRecipesSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.id).count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингрединтов."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания ингредиента рецепта."""

    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""

    author = FoodgramUserSerializer(read_only=True)
    image = Base64ImageField(
        required=False,
        allow_null=True
    )
    ingredients = RecipeIngredientsSerializer(
        source='recipeingredients',
        many=True,
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shop_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shop_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Favourites.objects.filter(
            recipe=obj, user=user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and ShopCart.objects.filter(
            user=user, recipe=obj
        ).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""

    image = Base64ImageField()
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all()),
        write_only=True
    )
    author = FoodgramUserSerializer(read_only=True)
    ingredients = serializers.ListField(
        child=RecipeIngredientCreateSerializer(),
        write_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте ингредиенты')
        ingredients_list = []
        for ingredient in ingredients:
            amount = ingredient['amount']
            if amount < 1:
                raise serializers.ValidationError(
                    'Добавьте количество ингредиента')
            if ingredient in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться')
            ingredients_list.append(ingredient)
        if data['cooking_time'] < 1:
            raise serializers.ValidationError(
                'Добавьте время приготовления')
        if not data['tags']:
            raise serializers.ValidationError(
                'Добавьте тег')
        return data

    def add_tags_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self.add_tags_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        RecipeIngredients.objects.filter(recipe=instance).delete()
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        self.add_tags_ingredients(
            tags=tags, ingredients=ingredients, recipe=instance
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
