from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

router = DefaultRouter()
router.register(
    r'tags',
    TagViewSet,
    basename='tag'
)
router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredient'
)
router.register(
    r'recipes',
    RecipeViewSet,
    basename='recipe'
)

urlpatterns = [
    path('', include(router.urls)),
]
