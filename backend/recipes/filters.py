from django_filters import rest_framework as filters
from tags.models import Tag

from .models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")
    is_favorited = filters.BooleanFilter(method="filter_favorites")
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
        conjoined=False,
    )

    class Meta:
        model = Recipe
        fields = [
            "tags",
            "author",
            "is_in_shopping_cart",
            "is_favorited",
        ]

    def filter_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(recipes_in_shopping_cart__user=self.request.user)
        return queryset

    def filter_favorites(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_subscriptions(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(subscription__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
