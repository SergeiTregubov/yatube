# Generated by Django 2.2.19 on 2022-11-23 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_comment_follow'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created'], 'verbose_name': 'Коментарий', 'verbose_name_plural': 'Коментарии'},
        ),
    ]
