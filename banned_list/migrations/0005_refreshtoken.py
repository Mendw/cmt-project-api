# Generated by Django 3.1.1 on 2020-09-21 23:05

import datetime
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('banned_list', '0004_auto_20200918_1551'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefreshToken',
            fields=[
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('expiration', models.DateTimeField(default=datetime.datetime(2020, 9, 21, 19, 7, 54, 693877), editable=False)),
            ],
        ),
    ]
