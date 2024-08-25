from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class FoodgramUser(AbstractUser):
    """Модель пользователя Фудграм."""

    email = models.EmailField(
        'Почта',
        unique=True,
    )
    username = models.CharField(
        'Никнейм',
        max_length=settings.MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator(),],
    )
    password = models.CharField(
        'Пароль',
        max_length=settings.MAX_LENGTH,
        null=False,
        blank=False,
    )
    first_name = models.CharField(
        'Имя',
        max_length=settings.MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.MAX_LENGTH,
    )
    avatar = models.ImageField(
        'Фото',
        upload_to='users/avatars',
        null=True,
        blank=True
    )

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['email']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class FoodgramFollow(models.Model):
    """Модель подписки пользователя Фудграм."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow',
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
