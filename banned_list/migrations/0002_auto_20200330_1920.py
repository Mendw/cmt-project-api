# Generated by Django 3.0.4 on 2020-03-30 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banned_list', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='banned',
            name='extra_info',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='banned',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='banned',
            name='program',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='banned',
            name='source',
            field=models.CharField(max_length=255),
        ),
    ]
