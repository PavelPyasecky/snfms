from django.db import models

from db.database.model_base import SchemaModel


class UserAttribute(SchemaModel):
    user_attribute_id = models.AutoField(db_column='UserAttributeID', primary_key=True)
    user = models.ForeignKey('User', db_column="UserID", related_name='attributes', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50, blank=True)
    value = models.TextField(db_column='NameValue', blank=True)

    class Meta(SchemaModel.Meta):
        managed = True
        db_table = 'UserAttribute'
