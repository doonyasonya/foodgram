import io
import logging
from http import HTTPStatus

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning

from utils.mixins import APIVersionMixin
from .filters import IngredientFilter, RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLink,
)
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartCreateSerializer,
    ShoppingCartSerializer,
)
from .utils import code_generator

logger = logging.getLogger(__name__)
pdfmetrics.registerFont(TTFont("Arial", "data/arial.ttf"))


class RecipeViewSet(APIVersionMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.order_by("id")
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    versioning_class = AcceptHeaderVersioning

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get(self, request, *args, **kwargs):
        return self.get_versioned_response(request)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        long_link = f"/api/recipes/{recipe.id}/"
        short_link = ShortLink.objects.filter(long_url=long_link).first()
        if not short_link:
            short_link = ShortLink.objects.create(
                long_url=long_link, short_code=code_generator()
            )
        return Response(
            {"short-link": f"/s/{short_link.short_code}"},
            status=status.HTTP_200_OK
        )

    def _handle_post_request(self, request, pk, model, serializer_class):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        instance, created = model.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        serializer = serializer_class(instance)
        response = serializer.data
        return Response(
            response,
            status=(
                status.HTTP_201_CREATED
                if created else HTTPStatus.BAD_REQUEST
            ),
        )

    def _handle_delete_request(self, request, pk, model):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        instance = model.objects.filter(user=user, recipe=recipe)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Recipe not found in the list"},
            status=HTTPStatus.BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def shopping_cart(self, request, pk=None):
        return self._handle_post_request(
            request, pk, ShoppingCart, ShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._handle_delete_request(request, pk, ShoppingCart)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        return self._handle_post_request(
            request, pk, Favorite, FavoriteRecipeSerializer
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        return self._handle_delete_request(request, pk, Favorite)

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        buffer = io.BytesIO()
        elements = self._generate_shopping_list_elements(request.user)
        self._build_pdf(buffer, elements)
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename="shopping_cart.pdf"
        )

    def _generate_shopping_list_elements(self, user):
        ingredients = self._get_aggregated_ingredients(user)
        styles = getSampleStyleSheet()
        styles["Normal"].fontName = "Arial"
        elements = []

        if ingredients:
            elements.append(Paragraph("Список покупок:", styles["Normal"]))
            elements.append(Spacer(1, 12))
            elements.extend(
                self._create_ingredient_paragraphs(
                    ingredients,
                    styles
                )
            )
        else:
            elements.append(
                Paragraph("Список покупок пуст!", styles["Normal"])
            )

        return elements

    def _get_aggregated_ingredients(self, user):
        return (
            RecipeIngredient.objects.filter(
                recipe__in=user.recipes_shopping_cart.values_list(
                    "recipe", flat=True
                )
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

    def _create_ingredient_paragraphs(self, ingredients, styles):
        paragraphs = []
        for i, ingredient in enumerate(ingredients, start=1):
            text = (
                f'{i}. {ingredient["ingredient__name"]} - '
                f'{ingredient["total_amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}.'
            )
            paragraphs.extend(
                [Paragraph(text, styles["Normal"]), Spacer(1, 12)]
            )
        return paragraphs

    def _build_pdf(self, buffer, elements):
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18,
        )
        doc.build(elements)


class IngredientViewSet(APIVersionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = IngredientFilter
    pagination_class = None
    versioning_class = AcceptHeaderVersioning

    def get(self, request, *args, **kwargs):
        return self.get_versioned_response(request)


class FavoriteRecipeViewSet(APIVersionMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]
    versioning_class = AcceptHeaderVersioning

    def get_serializer_class(self):
        return (
            FavoriteRecipeSerializer
            if self.action in ("create", "destroy")
            else RecipeReadSerializer
        )

    def get(self, request, *args, **kwargs):
        return self.get_versioned_response(request)

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            data={"user": request.user.id, "recipe": instance.id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {"detail": "Recipe is already in favorites."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ShoppingCartViewSet(APIVersionMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    versioning_class = AcceptHeaderVersioning

    def get_serializer_class(self):
        return (
            ShoppingCartSerializer
            if self.action in ["list", "retrieve"]
            else ShoppingCartCreateSerializer
        )

    def get(self, request, *args, **kwargs):
        return self.get_versioned_response(request)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)


class ShoppingCartReadViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
