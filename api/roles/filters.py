import django_filters

from db.customer.models import Roles


class RolesFilterSet(django_filters.FilterSet):
    role_id = django_filters.NumberFilter(lookup_expr='exact')
    name = django_filters.CharFilter(lookup_expr='contains')
    description = django_filters.CharFilter(lookup_expr='contains')

    class Meta:
        fields = (
            'role_id',
            'name',
            'description',
        )
        model = Roles
