from api.generics import NoCacheListCreateAPIView, NoCacheRetrieveUpdateDeleteAPIView
from api.messages.filters import MessageFilterSet
from api.messages.serializers import MessageListSerializer
from api.mixins import CustomerMixin, RequestArgMixin
from db.customer.models import Message
from tools import IsAuthenticatedOrOptions


class MessageList(NoCacheListCreateAPIView, CustomerMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = MessageListSerializer
    filter_class = MessageFilterSet

    def get_queryset(self):
        return self.qs(Message).filter(created_by_id=self.user.pk)


class MessageDetail(NoCacheRetrieveUpdateDeleteAPIView, CustomerMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = MessageListSerializer
    filter_class = MessageFilterSet

    def get_queryset(self):
        return self.qs(Message).filter(created_by_id=self.user.pk)
