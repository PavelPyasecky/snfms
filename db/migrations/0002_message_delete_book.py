# Generated by Django 4.0.2 on 2022-05-05 22:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('message_id', models.AutoField(db_column='MessageID', primary_key=True, serialize=False)),
                ('message_text', models.CharField(blank=True, db_column='MessageText', max_length=1000)),
                ('created_by_id', models.IntegerField(blank=True, db_column='CreatedByID', null=True)),
                ('created_date', models.DateTimeField(blank=True, db_column='CreatedDate', null=True)),
                ('updated_id', models.IntegerField(blank=True, db_column='UpdatedID', null=True)),
                ('updated_date', models.DateTimeField(blank=True, db_column='UpdatedDate', null=True)),
                ('recipient', models.ForeignKey(db_column='Recipient', on_delete=django.db.models.deletion.PROTECT, related_name='recipient_messages', to='db.user')),
                ('sender', models.ForeignKey(db_column='Sender', on_delete=django.db.models.deletion.PROTECT, related_name='my_messages', to='db.user')),
            ],
            options={
                'db_table': 'Books',
                'ordering': ['pk'],
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='Book',
        ),
    ]
