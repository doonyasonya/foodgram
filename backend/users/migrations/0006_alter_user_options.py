# Generated by Django 4.2.16 on 2024-12-03 22:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_avatar'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'Пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
    ]
