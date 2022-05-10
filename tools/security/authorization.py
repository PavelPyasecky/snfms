from db.customer.models import UserAttribute, UserRole, RoleAttribute, User, Roles
from db.controller.models import Customer
from api.queryables import CustomerQueryable
from typing import Set


class UserSecurityAttributesProvider(CustomerQueryable):

    def __init__(self, customer: Customer):
        super().__init__(customer.domain_name)
        self.customer = customer

    def get_security_settings(self, user: User) -> Set[str]:
        user_security = self.qs(UserAttribute).filter(
            user_id=user.pk,
            name__istartswith='security.',
            value='True',
        ).values_list('name', flat=True)

        user_roles = self.qs(UserRole).filter(
            user_id=user.pk,
        ).values_list('role_id', flat=True)

        valid_role_ids = self.qs(Roles).filter(
            role_id__in=user_roles,
        ).values_list('role_id', flat=True)

        role_security = self.qs(RoleAttribute).filter(
            role_id__in=valid_role_ids,
            name__istartswith='security.',
            name_value='True',
        ).values_list('name', flat=True)

        attributes = set(user_security).union(set(role_security))
        return attributes
