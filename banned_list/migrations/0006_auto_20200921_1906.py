# Generated by Django 3.1.1 on 2020-09-21 23:06

import banned_list.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banned_list', '0005_refreshtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refreshtoken',
            name='expiration',
            field=models.DateTimeField(default=banned_list.models.token_expiration, editable=False),
        ),
    ]