# Generated by Django 3.1.1 on 2020-10-13 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banned_list', '0011_datalist_not_parsed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datalist',
            name='not_parsed',
        ),
        migrations.AddField(
            model_name='datalist',
            name='parsed',
            field=models.BooleanField(default=False),
        ),
    ]
