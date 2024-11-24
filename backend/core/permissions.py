from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
    IsAuthenticated
)


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class IsOwnerOrReadOnly(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user
