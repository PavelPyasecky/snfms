# Generated by Django 4.0.2 on 2022-05-05 23:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0003_alter_message_options_alter_message_table'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['pk']},
        ),
    ]
