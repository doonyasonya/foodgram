import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = (
            'email',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        # print(self, '123')
        # current_user = self.context['request'].user
        # if current_user.is_authenticated:
        #     return Subscription.objects.filter(
        #         user=current_user,
        #         author=obj
        #     ).exists()
        return False


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField()

    def validate_avatar(self, value):
        try:
            format, imgstr = value.split(';base64,')
            if format.split('/')[0] != 'data:image':
                raise serializers.ValidationError(
                    'Неверный формат изображения'
                )
            return ContentFile(base64.b64decode(imgstr), name='avatar.png')
        except Exception:
            raise serializers.ValidationError(
                'Ошибка при обработке изображения'
            )

    def save(self, **kwargs):
        user = self.context['request'].user
        user.avatar.save(
            self.validated_data['avatar'].name,
            self.validated_data['avatar'], save=True
        )
        return user.avatar.url


class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Неверный текущий пароль'
            )
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
