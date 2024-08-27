from django.contrib import admin

from .models import (
    Ingredient,
    Tag,
    RecipeIngredients,
    Recipe,
    ShopCart,
    Favourites,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'image',
        'text',
        'ingredients',
        'tags',
        'cooking_time',
        'pub_date',
        'favourites'
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )
    readonly_fields = ('favourites')

    @admin.display(description='Количество в избранном')
    def favourites(self, obj):
        return obj.favourite_recipe.count()


@admin.register(ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'recipe',
    )


@admin.register(Favourites)
class FavouritesAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'recipe',
    )
