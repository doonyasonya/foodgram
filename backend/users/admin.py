from django.contrib import admin

from .models import FoodgramUser, FoodgramFollow


@admin.register(FoodgramUser)
class FoodgramUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name'
    )
    list_filter = (
        'email',
        'username'
    )


@admin.register(FoodgramFollow)
class FoodgramFollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )
