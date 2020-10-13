from banned_list.models import BannedEntity, Alias, Profile, Parser, DataList, Event
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import generics
from unidecode import unidecode
from datetime import datetime
import json


class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alias
        fields = ['alias']


class BannedEntitySerializer(serializers.ModelSerializer):
    aliases = AliasSerializer(many=True, allow_null=True)
    data_list = serializers.StringRelatedField()

    class Meta:
        model = BannedEntity
        exclude = ['name_unidecoded']

    def validate_location(self, value):
        if not value or not type(value) == str:
            return None

        return value

    def validate_name(self, value):
        if type(value) == str and len(value) > 255:
            return value[:255]

        return value

    def create(self, validated_data):
        aliases = validated_data.pop('aliases')

        unidecoded = unidecode(
            validated_data['name']) if validated_data['name'] != None else None
        validated_data['name_unidecoded'] = unidecoded if unidecoded != validated_data['name'] else None

        banned_entity = BannedEntity.objects.create(  # pylint: disable=no-member
            **validated_data)
        for alias in aliases:
            unidecoded = unidecode(alias['alias'])
            if alias == unidecoded:
                unidecoded = None
            Alias.objects.create(alias=alias['alias'], alias_unidecoded=unidecoded,  # pylint: disable=no-member
                                 banned=banned_entity)
        return banned_entity


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['has_searched']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'first_name',
                  'last_name', 'email', 'profile', 'is_staff']


class ParserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parser
        fields = '__all__'


class DataListSerializer(serializers.ModelSerializer):
    parser = ParserSerializer()
    parse_file = serializers.FileField(use_url=False, required=False)

    class Meta:
        model = DataList
        fields = '__all__'


class DataListCreateUpdateSerializer(serializers.ModelSerializer):
    parser = serializers.PrimaryKeyRelatedField(
        queryset=Parser.objects.all())  # pylint: disable=no-member
    parse_file = serializers.FileField(required=False)
    filename = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = DataList
        fields = '__all__'

    def validate_filename(self, value):
        if default_storage.exists(value):
            return value

        raise serializers.ValidationError('File does not exist')

    def save(self, **kwargs):
        if 'filename' in self.validated_data or 'name' in self.validated_data:
            self.validated_data['parsed'] = False

        if 'filename' in self.validated_data:
            filename = self.validated_data.pop('filename')
            self.validated_data['parse_file'] = default_storage.open(filename)

            if self.instance is not None:
                self.instance.uploaded = datetime.now()
                if (self.instance.parse_file and filename != self.instance.parse_file.name):
                    try:
                        self.instance.parse_file.delete(save=False)
                    except Exception:
                        pass

        super().save(**kwargs)


class EventSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
