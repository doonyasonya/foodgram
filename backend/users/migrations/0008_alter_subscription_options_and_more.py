# Generated by Django 4.2.14 on 2024-09-15 19:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_alter_subscription_subscribed_to_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="subscription",
            options={
                "verbose_name": "Подписка",
                "verbose_name_plural": "Подписки",
            },
        ),
        migrations.AlterUniqueTogether(
            name="subscription",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="subscribed_to",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="users_subscribers",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Автор",
            ),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="users_subscriptions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Юзверь",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(max_length=150, verbose_name="Имя"),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(max_length=150, verbose_name="Фамилия"),
        ),
        migrations.AddConstraint(
            model_name="subscription",
            constraint=models.UniqueConstraint(
                fields=("user", "subscribed_to"),
                name="unique_subscription_users",
            ),
        ),
    ]