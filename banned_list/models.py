from django.db import models

class BannedEntity(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    dob = models.DateField()
    is_sanctioned = models.BooleanField()
    extra_info = models.TextField(null=True)

    class Meta:
        verbose_name = 'Banned Entity'
        verbose_name_plural = "Banned Entities"

class Alias(models.Model):
    alias = models.CharField(max_length=255)
    banned = models.ForeignKey( 
        BannedEntity,
        on_delete=models.CASCADE,
        related_name='aliases'
    )