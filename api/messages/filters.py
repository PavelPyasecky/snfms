import django_filters

from db.customer.models import Message


class MessageFilterSet(django_filters.FilterSet):
    message_text = django_filters.CharFilter(lookup_expr='contains')
    recipient = django_filters.NumberFilter(lookup_expr='exact')

    class Meta:

        fields = (
            'message_text',
            'recipient',
        )
        model = Message
