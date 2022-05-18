from django.db import models
from sqlparse.utils import offset

from db.database.model_base import SchemaModel

from db.customer.models.users import *
from db.customer.models.message import *


class UserRole(SchemaModel):
    user_roles_id = models.AutoField(db_column='UserRolesID', primary_key=True)
    user = models.ForeignKey('User', db_column='UserID', blank=True, null=True, on_delete=models.DO_NOTHING)
    role = models.ForeignKey('Roles', db_column='RoleID', blank=True, null=True, on_delete=models.CASCADE)

    class Meta(SchemaModel.Meta):
        # managed = False
        db_table = 'UserRoles'


class Roles(SchemaModel):
    ADMIN_NAVIGATION = 'Admin Navigation'
    ADMIN_ROLE = 'Admin Role'

    HAS_ACCESS_TRUE = 'True'
    HAS_ACCESS_FALSE = 'False'

    role_id = models.AutoField(db_column='RoleID', primary_key=True)
    name = models.CharField(db_column='RoleName', max_length=50, blank=True)
    description = models.CharField(db_column='RoleDescription', max_length=500, blank=True)
    created_by = models.ForeignKey('User', db_column='CreatedByID', blank=True, null=True,
                                   related_name='roles_created', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(db_column='CreatedDate', blank=True, null=True, default=offset)
    updated_by = models.ForeignKey('User', db_column='UpdatedByID', blank=True, null=True,
                                   related_name='roles_updated', on_delete=models.DO_NOTHING)
    updated_date = models.DateTimeField(db_column='UpdatedDate', blank=True, null=True, default=offset)
    data_access = models.BooleanField(db_column='DataAccess', blank=True)
    menu_access = models.BooleanField(db_column='MenuAccess', blank=True)
    dashboard_access = models.BooleanField(db_column='DashboardAccess', blank=True)
    report_access = models.BooleanField(db_column='ReportAccess', blank=True)
    cases = models.BooleanField(db_column='Cases', blank=True)

    class Meta(SchemaModel.Meta):
        # managed = False
        db_table = 'Roles'


class RoleAttribute(SchemaModel):
    NAME_VALUE_TRUE = 'True'
    NAME_VALUE_FALSE = 'False'

    role_attribute_id = models.AutoField(db_column='RoleAttributeID', primary_key=True)
    role_id = models.IntegerField(db_column='RoleID', blank=True, null=True)
    name = models.CharField(max_length=50, blank=True)

    name_value = models.BooleanField(db_column='nameValue', blank=True)

    class Meta(SchemaModel.Meta):
        # managed = False
        db_table = 'RoleAttribute'
