from rest_framework import serializers
from banned_list.models import BannedEntity, Alias
from rest_framework import generics
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


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
    password1 = serializers.CharField(max_length=128, style={'input_type': 'password'})
    password2 = serializers.CharField(max_length=128, style={'input_type': 'password'})

    form = UserCreationForm

    def create(self, validated_data):
        validated_data['password1'] = validated_data['password1'].lower()
        validated_data['password2'] = validated_data['password2'].lower()
        self.form(data=validated_data).save()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'