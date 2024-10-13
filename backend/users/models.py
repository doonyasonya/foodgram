from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import MAX_LENGTH_FIRST, MAX_LENGTH_NAME


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_FIRST,
        verbose_name="Фамилия",
    )
    avatar = models.ImageField(
        verbose_name="Аватар",
        upload_to="avatars/",
        default="avatars/default_avatar.png",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Пользователи",
        related_name="users_subscriptions",
        on_delete=models.CASCADE,
    )
    subscribed_to = models.ForeignKey(
        User,
        verbose_name="Автор",
        related_name="users_subscribers",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscribed_to"],
                name="unique_subscription_users",
            )
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user.username} {self.subscribed_to.username}"
