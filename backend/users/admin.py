from django.contrib import admin

from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
    )
    search_fields = (
        'email',
        'username',
    )
    list_editable = (
        'first_name',
        'last_name',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
    )
    ordering = (
        'email',
    )
    readonly_fields = (
        'last_login',
        'date_joined',
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    search_fields = (
        'user__username',
        'author__username',
    )
    list_filter = (
        'user',
        'author',
    )
    ordering = (
        'user',
    )
