# Generated by Django 4.2.14 on 2024-09-12 19:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("recipes", "0008_alter_recipe_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="favorite",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favorites_recipes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="measurement_unit",
            field=models.CharField(
                max_length=200, verbose_name="Ед. измерения"
            ),
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="name",
            field=models.CharField(max_length=200, verbose_name="Название"),
        ),
    ]
