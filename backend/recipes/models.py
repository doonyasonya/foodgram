from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from users.models import FoodgramUser


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        'Название ингредиента',
        max_length=settings.MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=settings.MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент',
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Тэги для удобной фильтрации."""

    name = models.CharField(
        'Тэг',
        max_length=settings.MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг тэга',
        max_length=settings.MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тэг',
        verbose_name_plural = 'Тэги'
        ordering = ('slug',)

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """Ингредиенты в рецепте."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class Recipe(models.Model):
    """Рецепт блюда."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название блюда',
        max_length=settings.MAX_LENGTH,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images'
    )
    text = models.CharField(
        'Описание блюда',
        max_length=settings.MAX_LENGTH,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredients,
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
    )
    cooking_time = models.IntegerField(
        'Время готовки',
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField(
        'Создано в',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class ShopCart(models.Model):
    """Корзина."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        return f'{self.author} добавил: {self.recipe}'


class Favourites(models.Model):
    """Избранное."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favourite_recipe'
    )

    class Meta:
        abstract = True
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return self.recipe
