# Generated by Django 2.0.5 on 2020-10-22 09:39

from django.db import migrations
import embed_video.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20201022_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='video',
            field=embed_video.fields.EmbedVideoField(blank=True, verbose_name='Видео'),
        ),
    ]
