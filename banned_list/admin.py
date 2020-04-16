from django.contrib import admin

from .models import BannedEntity, Alias
# Register your models here.

admin.site.register(BannedEntity)
admin.site.register(Alias)