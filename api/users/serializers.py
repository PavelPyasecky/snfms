from django.core.validators import EmailValidator
from rest_framework import serializers, relations, exceptions
from rest_framework.validators import UniqueValidator

from django.contrib.auth.models import User as UserAuth

from db import get_customer_domain_from_request
from db.customer.models import User, Roles, UserRole


class BaseUsersSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation

    class Meta:
        model = User


class UsersListSerializer(BaseUsersSerializer):

    url = relations.HyperlinkedIdentityField(view_name='users:detail')
    default_role = serializers.IntegerField(write_only=True, required=False)

    def create(self, validated_data):
        validated_data['customer_id'] = self.context['view'].customer.pk

        if 'name' not in validated_data:
            first_name_presented = 'first_name' in validated_data and bool(validated_data['first_name'])
            last_name_presented = 'last_name' in validated_data and bool(validated_data['last_name'])
            if first_name_presented ^ last_name_presented:
                validated_data['name'] = validated_data.get('first_name', '') + validated_data.get('last_name', '')
            elif first_name_presented and last_name_presented:
                validated_data['name'] = f"{validated_data['first_name']} {validated_data['last_name']}"

        default_role = validated_data.pop('default_role', None)
        if default_role:
            try:
                role = Roles.objects.get(role_id=default_role)
            except Roles.DoesNotExist:
                raise exceptions.ValidationError({"default_role": "Role does not exist."})
            user_instance = super(UsersListSerializer, self).create(validated_data)
            UserRole.objects.create(
                user=user_instance,
                role=role
            )
        else:
            user_instance = super(UsersListSerializer, self).create(validated_data)



        return user_instance

    class Meta:
        restricted_fields = (
            'picture',  # todo binary fields are acting strange, read only no matter what
            'crypt_password',  # todo binary fields are acting strange, read only no matter what
            'password_size',
            'customer_id',
            'hashed_key',
        )

        fields = (
            'url',
            'default_role',
        ) + tuple(set(User._get_model_field_names()) - set(restricted_fields))

        extra_kwargs = {
            'user_id': {'read_only': True},

            'name': {'write_only': True},
            'address1': {'write_only': True, 'required': False},
            'address2': {'write_only': True, 'required': False},
            'city': {'write_only': True, 'required': False},
            'state': {'write_only': True, 'required': False},
            'zip': {'write_only': True, 'required': False},
            'country': {'write_only': True, 'required': False},
            'phone_number': {'write_only': True, 'required': False},
            'primary_contact': {'write_only': True, 'required': False},
            'admin': {'write_only': True, 'required': False},
            'crm_id': {'write_only': True, 'required': False},
            'job_title': {'write_only': True, 'required': False},
            'linked_in': {'write_only': True, 'required': False},
            'twitter': {'write_only': True, 'required': False},
            'face_book': {'write_only': True, 'required': False},
            'bio': {'write_only': True, 'required': False},
            'salutation': {'write_only': True, 'required': False},
            'phone_extension': {'write_only': True, 'required': False},
            'cell': {'write_only': True, 'required': False},
            'letter_closing': {'write_only': True, 'required': False},
            'company_website': {'write_only': True, 'required': False},
            'profile_picture': {'write_only': True, 'required': False},

            # Username should be required and cannot be blank
            'user_name': {'required': True, 'allow_blank': False},
        }
        model = User


class UsersDetailSerializer(BaseUsersSerializer):

    url = relations.HyperlinkedIdentityField(view_name='users:detail')
    admin_check = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        if 'name' not in validated_data:
            first_name_presented = 'first_name' in validated_data
            last_name_presented = 'last_name' in validated_data

            if first_name_presented:
                instance.first_name = validated_data['first_name']
            if last_name_presented:
                instance.last_name = validated_data['last_name']

            if instance.first_name and instance.last_name:
                validated_data['name'] = f'{instance.first_name} {instance.last_name}'
            else:
                validated_data['name'] = instance.first_name + instance.last_name
        return super(UsersDetailSerializer, self).update(instance, validated_data)

    def get_admin_check(self, obj):
        return self.context['view'].admin_role_check()

    def get_domain(self, obj):
        return get_customer_domain_from_request(self.context['request'])

    class Meta:
        restricted_fields = (
            'picture',  # todo binary fields are acting strange
            'crypt_password',  # todo binary fields are acting strange
            'password_size',
            'customer_id',
            'hashed_key',
        )

        fields = (
            'url',
        ) + tuple(set(User._get_model_field_names()) - set(restricted_fields)) + (
            'admin_check',
            'domain',
        )

        model = User

        extra_kwargs = {
            # read only
            'user_id': {'read_only': True},
            'customer_id': {'read_only': True},
            'crm_id': {'read_only': True},
            "admin": {'read_only': True},
            'status': {'read_only': True},

            # validators
            'email': {'validators': [
                UniqueValidator(
                    queryset=model.objects.all()
                ),
                EmailValidator(),
            ]
            }
        }
