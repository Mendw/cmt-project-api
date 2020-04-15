from rest_framework import serializers
from banned_list.models import BannedEntity, Alias
from rest_framework import generics
from django.contrib.auth.models import User


class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alias
        fields = 'all'


class BannedEntitySerializer(serializers.ModelSerializer):
    aliases = AliasSerializer()

    class Meta:
        model = BannedEntity
        fields = ['name', 'location', 'source',
                  'dob', 'is_sanctioned', 'extra_info', 'aliases']


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=256)

    def create(self, validated_data):
        password = validated_data.pop('password').lower()
        return User.objects.create_user(password=password, **validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'