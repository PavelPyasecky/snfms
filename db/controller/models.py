from django.db import models

from db.database.model_base import SchemaModel


class Customer(SchemaModel):
    customer_id = models.IntegerField(db_column='Customer_id', primary_key=True)
    customer_name = models.CharField(db_column='CustomerName', max_length=50, blank=True)
    domain_name = models.CharField(db_column='DomainName', max_length=50, blank=True)
    process_active = models.IntegerField(db_column='ProcessActive', blank=True, null=True)
    sql_connect_string = models.CharField(db_column='SQLConnectString', max_length=200, blank=True)

    class Meta(SchemaModel.Meta):
        managed = False
        db_table = 'Customer'
