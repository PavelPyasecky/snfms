from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.generics import NoCacheListCreateAPIView
from api.messages.serializers import MessageListSerializer
from api.mixins import CustomerMixin
from db.customer.models import Message, User
from tools.query import get_object_or_404_with_message


class MessageList(NoCacheListCreateAPIView, CustomerMixin):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = MessageListSerializer

    def get_recipient(self):
        return get_object_or_404_with_message("Recipient with such user_id doesn't exist.")(self.qs(User),
                                                                                            user_id=self.kwargs['user_id'])

    def get_queryset(self):
        return self.qs(Message).filter(sender=self.user.pk, recipient=self.get_recipient().pk)
