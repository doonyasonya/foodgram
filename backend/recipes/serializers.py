import uuid
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
)
from users.serializers import UserSerializer
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, base64_data = data.split(';base64,')
            extension = header.split('/')[-1]
            unique_name = f'{uuid.uuid4()}.{extension}'
            decoded_file = ContentFile(
                base64.b64decode(base64_data),
                name=unique_name
            )
            data = decoded_file
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipeFavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'cooking_time',
            'image',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True,
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True,
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'author',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.favorited_by.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.shopping_cart.filter(
                recipe=obj
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'author',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate(self, data):
        self._validate_tags(data.get('tags', []))
        self._validate_ingredients(data.get('recipeingredient_set', []))
        self._validate_cooking_time(data.get('cooking_time'))
        self._validate_image(data.get('image'))
        return data

    def _validate_tags(self, tags):
        if not tags:
            raise ValidationError(
                {'tags': 'Поле Тег пустое'}
            )

        tag_ids = {tag.id for tag in tags}
        if len(tags) != len(tag_ids):
            raise ValidationError(
                {'tags': 'Теги должны быть уникальными'}
            )

    def _validate_ingredients(self, ingredients):
        ingredient_ids = {ing['ingredient'].id for ing in ingredients}
        if len(ingredients) != len(ingredient_ids):
            raise ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться'}
            )

    def _validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise ValidationError(
                {'cooking_time': 'Время приготовления должно быть больше 0'}
            )

    def _validate_image(self, image):
        if not image:
            raise ValidationError(
                {'image': 'Необходимо предоставить изображение'}
            )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', [])
        tags_data = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user

        if not ingredients_data:
            raise ValidationError('Нет ингредиентов')

        for data in ingredients_data:
            amount = data.get('amount', 0)
            if amount < 1:
                raise ValidationError(
                    {'amount': 'Количество должно быть больше 0'}
                )

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        ingredients_to_create = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=data.pop('ingredient'),
                **data
            )
            for data in ingredients_data
        ]

        RecipeIngredient.objects.bulk_create(ingredients_to_create)
        return recipe

    def get_is_favorited(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.favorited_by.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.shopping_cart.filter(
                recipe=obj
            ).exists()
        )

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'author',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate(self, data):
        self._validate_tags(data.get('tags', []))
        self._validate_ingredients(data.get('recipeingredient_set', []))
        self._validate_cooking_time(data.get('cooking_time'))
        self._validate_image(data.get('image'))
        return data

    def _validate_tags(self, tags):
        if not tags:
            raise ValidationError(
                {'tags': 'Поле Тег пустое'}
            )

        tag_ids = {tag.id for tag in tags}
        if len(tags) != len(tag_ids):
            raise ValidationError(
                {'tags': 'Теги должны быть уникальными'}
            )

    def _validate_ingredients(self, ingredients):
        ingredient_ids = {ing['ingredient'].id for ing in ingredients}
        if len(ingredients) != len(ingredient_ids):
            raise ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться'}
            )

    def _validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise ValidationError(
                {'cooking_time': 'Время приготовления должно быть больше 0'}
            )

    def _validate_image(self, image):
        if not image:
            raise ValidationError(
                {'image': 'Необходимо предоставить изображение'}
            )

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', [])
        tags_data = validated_data.pop('tags', [])

        if not ingredients_data:
            raise ValidationError('Нет ингредиентов')
        if not tags_data:
            raise ValidationError('Нет тэгов')

        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredients.clear()

        ingredients_to_create = []
        for data in ingredients_data:
            ingredient = data.pop('ingredient')
            amount = data.get('amount')
            if amount < 1:
                raise ValidationError(
                    {'amount': 'Количество должно быть больше 0'}
                )
            new_ingredient = RecipeIngredient(
                recipe=instance,
                ingredient=ingredient,
                amount=amount
            )
            new_ingredient.full_clean()
            ingredients_to_create.append(new_ingredient)

        RecipeIngredient.objects.bulk_create(ingredients_to_create)
        return instance

    def get_is_favorited(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.favorited_by.filter(
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        author = self.context['request'].user
        return (
            author.is_authenticated
            and author.shopping_cart.filter(
                recipe=obj
            ).exists()
        )

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(
            user=user,
            author=obj
        ).exists()

    def validate_for_delete(self, user, author):
        if not Subscription.objects.filter(
            user=user,
            subscription_author=author
        ).exists():
            raise serializers.ValidationError('Подписка не найдена')

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        request = self.context.get('request')
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit is not None:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            else:
                recipes_limit = None
        return RecipeFavouriteSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_avatar(self, obj):
        return self.context['request'].build_absolute_uri(
            obj.avatar.url
        ) if obj.avatar else None

    def get_recipes_count(self, obj):
        return obj.recipes.count()
