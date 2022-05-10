from rest_framework import serializers

from db.customer.models.message import Message


class MessageListSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'message_id',
            'message_text',
            'sender',
            'recipient'
        )
        model = Message
