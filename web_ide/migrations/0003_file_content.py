# Generated by Django 4.2 on 2023-05-01 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_ide', '0002_alter_filesystemobject_availability_change_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='content',
            field=models.TextField(blank=True, default=''),
        ),
    ]
