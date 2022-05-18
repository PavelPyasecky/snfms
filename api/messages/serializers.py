from rest_framework import serializers

from api.serializers import AutoNowMixin, AutoUserMixin
from db.customer.models import Message, User


class MessageListSerializer(AutoNowMixin, AutoUserMixin, serializers.ModelSerializer):
    recipient_id = serializers.PrimaryKeyRelatedField(source='recipient', queryset=User.objects)

    def create(self, validated_data):
        validated_data['created_by_id'] = self.get_user_pk()
        validated_data['updated_by_id'] = self.get_user_pk()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by_id'] = self.get_user_pk()
        return super().update(instance, validated_data)

    class Meta:
        fields = (
            'message_id',
            'message_text',
            'recipient_id',
            'created_date',
            'created_by_id',
            'updated_by_id',
            'updated_date'
        )
        model = Message
        extra_kwargs = {
            'message_id': {'read_only': True},
            'recipient_id': {'read_only': True},
            'message_text': {'required': True},
        }
