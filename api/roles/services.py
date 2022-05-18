from collections import OrderedDict

from django.utils import timezone

from rest_framework import exceptions

from django.db import transaction

from api.queryables import CustomerQueryable
from db.customer.models import RoleAttribute, UserRole, Roles, User


class RoleCopyService(CustomerQueryable):
    def copy_role(self, user: User, role: Roles, validated_data: OrderedDict) -> Roles:
        """
        This method create a copy of the role, including related users and
        attributes
        """

        role_users = self.qs(UserRole).filter(role=role)
        role_attributes = self.qs(RoleAttribute).filter(role_id=role.role_id)

        role.role_id = None
        for attr, value in validated_data.items():
            setattr(role, attr, value)
        role.created_by = role.updated_by = user
        role.created_date = role.updated_date = timezone.now()

        with transaction.atomic(using=self.customer_domain):
            role.save()
            self._copy_related_entities(role_attributes, 'role_attribute_id', 'role_id', role.role_id)
            self._copy_related_entities(role_users, 'user_roles_id', 'role', role)

            attributes_to_log = list(attr.name for attr in role_attributes if
                                     attr.name_value == RoleAttribute.NAME_VALUE_TRUE)
            if role.data_access == Roles.HAS_ACCESS_TRUE:
                attributes_to_log.append("data_access")
            if role.menu_access == Roles.HAS_ACCESS_TRUE:
                attributes_to_log.append("menu_access")
        return role

    def _copy_related_entities(self, qs, id_field, role_field, role_value):
        objs = list(qs)
        for obj in objs:
            setattr(obj, id_field, None)
            setattr(obj, role_field, role_value)
        qs.bulk_create(objs)


def validate_unique(role_name, queryset):
    if queryset.filter(name=role_name).exists():
        raise exceptions.ValidationError({'detail': 'Name must be unique'})


class RoleAttributesService(CustomerQueryable):
    def __init__(self, customer):
        self.customer = customer
        super().__init__(customer_domain=self.customer.domain_name)

    def _get_navigation_permissions(self):
        return NavigationPermission.objects.using('sfcontroller').filter(attribute_name__in=list(
            ControllerAttribute.objects.using('sfcontroller').filter(
                customer=self.customer, source_value='True').values_list('source_name', flat=True)))

    def get_role_attributes(self):
        attributes = self._get_navigation_permissions().values('pk', 'parent', 'label', 'attribute_name', 'category')
        role_attributes = []
        parents = [attr for attr in attributes if attr['parent'] is None]
        for parent_attr in sorted(parents, key=lambda tup: tup['category']):
            role_attributes.append({"label": parent_attr['label'],
                                    "name": parent_attr['attribute_name'],
                                    "is_parent": True})
            role_attributes += [{"label": "%s - %s" % (sub_attr['category'],
                                                       sub_attr['label']),
                                 "name": sub_attr['attribute_name'], "is_parent": False}
                                for sub_attr in sorted(attributes, key=lambda tup: tup['label'])
                                if sub_attr['parent'] == parent_attr['pk']]
        return role_attributes
