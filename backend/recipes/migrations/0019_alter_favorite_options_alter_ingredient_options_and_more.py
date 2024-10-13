# Generated by Django 5.0.4 on 2024-10-12 19:56

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipes", "0018_alter_recipeingredient_ingredient"),
        ("tags", "0003_alter_tag_options"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="favorite",
            options={
                "verbose_name": "Избранное",
                "verbose_name_plural": "Избранные рецепты",
            },
        ),
        migrations.AlterModelOptions(
            name="ingredient",
            options={
                "verbose_name": "Ингредиент",
                "verbose_name_plural": "Ингредиенты",
            },
        ),
        migrations.AlterModelOptions(
            name="recipeingredient",
            options={
                "verbose_name": "Ингредиент в рецепте",
                "verbose_name_plural": "Ингредиенты в рецептах",
            },
        ),
        migrations.RemoveConstraint(
            model_name="shoppingcart",
            name="unique_shopping_cart",
        ),
        migrations.AlterField(
            model_name="favorite",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="in_favorites",
                to="recipes.recipe",
                verbose_name="Рецепт",
            ),
        ),
        migrations.AlterField(
            model_name="favorite",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_favorites",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="measurement_unit",
            field=models.CharField(max_length=200, verbose_name="Единица измерения"),
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="name",
            field=models.CharField(max_length=200, verbose_name="Название ингредиента"),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_recipes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Автор рецепта",
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="cooking_time",
            field=models.PositiveSmallIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(
                        1, message="Минимальное время готовки — 1 мин."
                    ),
                    django.core.validators.MaxValueValidator(
                        10000, message="Максимальное время готовки — 10000 мин."
                    ),
                ],
                verbose_name="Время приготовления (мин.)",
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="image",
            field=models.ImageField(
                upload_to="recipes/images/", verbose_name="Изображение рецепта"
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="ingredients",
            field=models.ManyToManyField(
                through="recipes.RecipeIngredient",
                to="recipes.ingredient",
                verbose_name="Ингредиенты",
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="name",
            field=models.CharField(max_length=256, verbose_name="Название рецепта"),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="tags",
            field=models.ManyToManyField(
                related_name="tagged_recipes", to="tags.tag", verbose_name="Теги"
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="text",
            field=models.TextField(verbose_name="Описание рецепта"),
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="amount",
            field=models.PositiveSmallIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(
                        1, message="Минимальное количество — 1"
                    ),
                    django.core.validators.MaxValueValidator(
                        10000, message="Максимальное количество — 10000"
                    ),
                ],
                verbose_name="Количество",
            ),
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="ingredient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="recipes.ingredient",
                verbose_name="Ингредиент",
            ),
        ),
        migrations.AlterField(
            model_name="shoppingcart",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="in_shopping_cart",
                to="recipes.recipe",
                verbose_name="Рецепт",
            ),
        ),
        migrations.AlterField(
            model_name="shoppingcart",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_shopping_cart",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppingcart",
            constraint=models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_cart_item"
            ),
        ),
    ]