from django.db import models

from .constants import MAX_LENGTH_NAME


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name="Название"
    )
    slug = models.SlugField(unique=True, verbose_name="Слаг")

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self):
        return self.name
