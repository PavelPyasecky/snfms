from django.db import models

from db.database.model_base import SchemaModel


class Message(SchemaModel):
    message_id = models.AutoField(db_column='MessageID', primary_key=True)
    message_text = models.CharField(db_column='MessageText', max_length=1000, blank=True)
    sender = models.ForeignKey('User', db_column='Sender', on_delete=models.PROTECT, related_name='my_messages')
    recipient = models.ForeignKey('User', db_column='Recipient', on_delete=models.PROTECT, related_name='recipient_messages')
    created_by_id = models.IntegerField(db_column='CreatedByID', blank=True, null=True)
    created_date = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)
    updated_id = models.IntegerField(db_column='UpdatedID', blank=True, null=True)
    updated_date = models.DateTimeField(db_column='UpdatedDate', blank=True, null=True)

    class Meta(SchemaModel.Meta):
        # managed = True
        db_table = 'Messages'
