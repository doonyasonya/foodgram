from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from tags.serializers import Tag, TagSerializer
from django.shortcuts import get_object_or_404
from users.models import Subscription, User
from users.serializers import UserSerializer

from .fields import ImageBaseField
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        source="recipeingredient_set", many=True
    )
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    image = ImageBaseField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_in_shopping_cart",
        )
        extra_kwargs = {
            "text": {"required": True},
            "name": {"required": True},
            "image": {"required": False, "allow_null": True},
            "cooking_time": {"required": True},
        }

    def validate(self, data):
        tags = data.get("tags", [])
        ingredients = data.get("recipeingredient_set", [])

        if not tags:
            raise ValidationError({"tags": "Поле Тег не может быть пустым."})

        if len(tags) != len(set(tag.id for tag in tags)):
            raise ValidationError({"tags": "Теги не должны дублироваться."})

        if len(ingredients) != len(
            set(ing["ingredient"].id for ing in ingredients)
        ):
            raise ValidationError(
                {"ingredients": "Ингредиенты не должны дублироваться."}
            )

        if not data.get("image"):
            raise ValidationError(
                {"image": "Изображение не может быть пустым."}
            )

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipeingredient_set", [])
        tags_data = validated_data.pop("tags", [])
        validated_data["author"] = self.context["request"].user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        if not ingredients_data:
            raise ValidationError("Ингредиенты отсутствуют.")

        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("recipeingredient_set", None)

        if not ingredients:
            raise ValidationError(
                {
                    "recipeingredient_set":
                    "Поле ingredients обязательно для обновления рецепта."
                }
            )
        if tags is None:
            raise ValidationError(
                {"tags": "Поле tags обязательно для обновления рецепта."}
            )

        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self._create_recipe_ingredients(instance, ingredients)
        return instance

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=data.pop("ingredient"), **data
            )
            for data in ingredients_data
        ]
        for ingredient in recipe_ingredients:
            try:
                ingredient.full_clean()
            except DjangoValidationError as e:
                raise ValidationError({"amount": e.messages})

        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.recipes_shopping_cart.filter(recipe=obj).exists()
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipeingredient_set", many=True
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = ImageBaseField(required=False, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        return self._check_related(obj, "favorites")

    def get_is_in_shopping_cart(self, obj):
        return self._check_related(obj, "recipes_shopping_cart")

    def _check_related(self, obj, related_name):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return getattr(request.user, related_name).filter(recipe=obj).exists()


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )
        read_only_fields = ("email", "username", "first_name", "last_name")

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.users_subscriptions.filter(subscribed_to=obj).exists()
        )

    def validate_for_delete(self, user, author):
        if not Subscription.objects.filter(
            user=user, subscribed_to=author
        ).exists():
            raise serializers.ValidationError("Подписка не найдена.")

    def get_recipes(self, obj):
        limit = self.context["request"].GET.get("recipes_limit")
        recipes = obj.recipes.all()[
            : int(limit)
        ] if limit else obj.recipes.all()
        return RecipeCustomSerializer(recipes, many=True, read_only=True).data

    def get_avatar(self, obj):
        return (
            self.context["request"].build_absolute_uri(obj.avatar.url)
            if obj.avatar
            else None
        )

    def validate(self, data):
        user = self.context["request"].user
        if user == self.instance:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )
        if Subscription.objects.filter(
            user=user, subscribed_to=self.instance
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )
        return data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        favorite = get_object_or_404(Favorite, pk=representation["id"])
        recipe = favorite.recipe
        short_serializer = RecipeCustomSerializer(recipe)
        return short_serializer.data

    def get_image(self, obj):
        if obj.image:
            return self.context["request"].build_absolute_uri(obj.image.url)
        return None


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes_limit = serializers.IntegerField(required=False, default=None)

    class Meta:
        model = Subscription
        fields = ("user", "recipes", "recipes_count")

    def get_user(self, obj):
        user = obj.user
        user_serializer = UserSerializer(user, context=self.context)
        return user_serializer.data

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.recipe.author)
        return RecipeCustomSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.recipe.author).count()


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )
        extra_kwargs = {
            "id": {"required": True},
        }

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user, subscribed_to=obj
        ).exists()

    def to_representation(self, instance):
        if isinstance(instance, User) and instance.is_anonymous:
            representation = super().to_representation(instance)
            representation.pop("email", None)
            return representation
        return super().to_representation(instance)


class RecipeShortSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def to_representation(self, instance):
        return {
            **super().to_representation(instance),
            "image": instance.image.url if instance.image else None,
        }


class RecipeCustomSerializer(ModelSerializer):
    image = ImageBaseField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class ShoppingCartCreateSerializer(ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("recipe",)


class ShoppingCartSerializer(ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ("recipe",)

    def to_representation(self, instance):
        return self.fields["recipe"].to_representation(instance.recipe)
