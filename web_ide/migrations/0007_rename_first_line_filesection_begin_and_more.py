# Generated by Django 4.2 on 2023-05-16 17:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('web_ide', '0006_file_compiled_content'),
    ]

    operations = [
        migrations.RenameField(
            model_name='filesection',
            old_name='first_line',
            new_name='begin',
        ),
        migrations.RenameField(
            model_name='filesection',
            old_name='last_line',
            new_name='end',
        ),
        migrations.AlterField(
            model_name='filesection',
            name='creation_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='date created'),
        ),
    ]
