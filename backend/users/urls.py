from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UsersViewSet

router = DefaultRouter()
router.register(
    r'users',
    UsersViewSet,
    basename='user'
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
