import django_filters

from db.customer.models import User


class UsersFilterSet(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr='contains')
    last_name = django_filters.CharFilter(lookup_expr='contains')
    email = django_filters.CharFilter(lookup_expr='contains')
    status = django_filters.CharFilter(method='filter_status')

    def filter_status(self, queryset, name, value):
        null_choice = -1
        for model_value, human_name in self.Meta.model.STATUS_CHOICES:
            if human_name.lower() == value.lower():
                return queryset.filter(**{name: model_value})
        return queryset.filter(**{name: null_choice})

    class Meta:

        fields = (
            'first_name',
            'last_name',
            'email',
            'status',
            'user_id',
        )
        model = User
