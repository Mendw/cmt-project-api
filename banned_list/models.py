from django.db.models.signals import pre_save, post_save, post_delete
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta


class DatabaseStatus(models.Model):
    is_available = models.BooleanField()
    locking_token = models.OneToOneField(
        'RefreshToken', on_delete=models.SET_NULL, null=True)


class BannedEntity(models.Model):
    name = models.CharField(max_length=255)
    name_unidecoded = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)
    data_list = models.ForeignKey(
        'DataList', on_delete=models.CASCADE, related_name='banned_entities')
    program = models.CharField(max_length=255, null=True)
    dob = models.DateField(null=True)
    dob_accuracy = models.BinaryField(max_length=2, null=True)
    is_sanctioned = models.TextField(max_length=4, default="Sí")

    class Meta:
        ordering = ['id']


class Alias(models.Model):
    alias = models.CharField(max_length=255)
    alias_unidecoded = models.CharField(max_length=255, null=True)
    banned = models.ForeignKey(
        BannedEntity,
        on_delete=models.CASCADE,
        related_name='aliases'
    )


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_searched = models.BooleanField(default=False)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)  # pylint: disable=no-member


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Parser(models.Model):
    name = models.CharField(max_length=127)
    class_name = models.CharField(max_length=31)
    reusable = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{0}({1})".format(self.name, self.class_name)


class DataList(models.Model):
    name = models.CharField(max_length=255)
    parser = models.ForeignKey(Parser, on_delete=models.CASCADE)
    parsed = models.BooleanField(default=False)
    parse_file = models.FileField()
    uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    event_type = models.CharField(
        max_length=8,
        choices=[
            ('created', 'object created'),
            ('deleted', 'object deleted'),
            ('modified', 'object modified'),
        ])

    description = models.TextField()
    object_name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


def token_expiration():
    return timezone.now() + timedelta(minutes=1)


class RefreshToken(models.Model):
    token = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    expiration = models.DateTimeField(default=token_expiration, editable=False)


@receiver(post_save, sender=DataList)
def post_data_list_modified(sender, instance: DataList, created, *args, **kwargs):
    action = 'created' if created else 'modified'
    event = Event(
        event_type=action,
        description="list '{0}' was {1}".format(
            instance.name,
            action),
        object_name=instance.name
    )

    event.save()


@receiver(post_delete, sender=DataList)
def post_data_list_deleted(sender, instance: DataList, **kwargs):
    if instance.parse_file and default_storage.exists(instance.parse_file.name):
        try:
            instance.parse_file.delete(save=False)
        except Exception:
            pass

    event = Event(
        event_type='deleted',
        description="list '{0}' was deleted".format(instance.name),
        object_name=instance.name
    )

    event.save()
