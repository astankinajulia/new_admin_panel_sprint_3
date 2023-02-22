# Generated by Django 3.2 on 2023-02-06 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0002_add_file_path_to_film_works'),
    ]

    operations = [
        migrations.RenameField(
            model_name='filmwork',
            old_name='type',
            new_name='film_type',
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='film_type',
            field=models.CharField(choices=[('MV', 'movie'), ('TS', 'tv_show')], db_column='type', max_length=2, verbose_name='type'),
        ),
        migrations.AlterField(
            model_name='personfilmwork',
            name='role',
            field=models.CharField(choices=[('actor', 'actor'), ('director', 'director'), ('writer', 'writer')], max_length=255, verbose_name='role'),
        ),
    ]