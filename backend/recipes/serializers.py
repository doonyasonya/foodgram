import uuid
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import (
    Recipe,
    Tag,
    Ingredient,
    # RecipeIngredient,
    # FavoriteRecipe,
    # ShoppingCart,
)
from users.serializers import UserSerializer

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
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'author',
            'image',
        )


class RecipeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
        )
