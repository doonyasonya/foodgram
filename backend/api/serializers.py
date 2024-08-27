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