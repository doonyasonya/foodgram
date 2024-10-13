from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.versioning import AcceptHeaderVersioning

from utils.mixins import APIVersionMixin

from .models import Tag
from .serializers import TagViewSerializer


class TagViewSet(APIVersionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by("id")
    serializer_class = TagViewSerializer
    versioning_class = AcceptHeaderVersioning
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return self.get_versioned_response(request)