from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from tags.models import Tag

from .constants import (
    INGREDIENT_NAME_LENGTH_LIMIT,
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MAX_UNIT_NAME_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    RECIPE_NAME_MAX_LENGTH,
)

User = get_user_model()


class ShortLink(models.Model):
    long_url = models.URLField()
    short_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.short_code} {self.long_url}"


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_LENGTH_LIMIT, verbose_name="Название"
    )
    measurement_unit = models.CharField(
        max_length=MAX_UNIT_NAME_LENGTH, verbose_name="Ед. измерения"
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], name="unique_favorite")
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"

    def __str__(self):
        return f"{self.user.username} {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes_shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="recipes_in_shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"{self.user.username} {self.recipe.name}"


class Recipe(models.Model):
    name = models.CharField(max_length=RECIPE_NAME_MAX_LENGTH, verbose_name="Имя")
    text = models.TextField(verbose_name="Текст")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Изображение")
    tags = models.ManyToManyField(Tag, related_name="recipes", verbose_name="Тэги")
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингридиенты"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время готовки",
        validators=[
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=f"Время должно быть не больше" f" {MAX_COOKING_TIME} минут",
            ),
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f"Время должно быть не меньше" f" {MIN_COOKING_TIME} минуты",
            ),
        ],
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def favorites_count(self):
        return self.favorited_by.count()

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингридиент",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Кол-во",
        validators=[
            MaxValueValidator(
                MAX_AMOUNT,
                message=f"Количество не может превышать {MAX_AMOUNT}",
            ),
            MinValueValidator(
                MIN_AMOUNT,
                message=f"Количество не может быть меньше {MIN_AMOUNT}",
            ),
        ],
    )

    class Meta:
        verbose_name = "Ингридиент рецепта"
        verbose_name_plural = "Ингридиенты рецептов"

    def __str__(self):
        return (
            f"{self.ingredient.name}"
            f"{self.amount} {self.ingredient.measurement_unit}"
        )
