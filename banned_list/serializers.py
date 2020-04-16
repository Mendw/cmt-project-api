from rest_framework import serializers
from banned_list.models import BannedEntity, Alias
from rest_framework import generics
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _


class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alias
        fields = '__all__'


class BannedEntitySerializer(serializers.ModelSerializer):
    aliases = AliasSerializer(many=True)

    class Meta:
        model = BannedEntity
        fields = ['name', 'location', 'source',
                  'dob', 'is_sanctioned', 'extra_info', 'aliases']


class SignupSerializer(serializers.Serializer):
    pass

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
