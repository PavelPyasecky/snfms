from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.validators import UniqueValidator

from api.serializer_fields import OptionsMappingField
from api.serializers import AutoNowMixin, AutoUserMixin
from db.customer.models import Roles, User, UserRole

from api.roles import exceptions
from api.users.exceptions import UserNotFoundException


class RolesBaseSerializer(AutoNowMixin, AutoUserMixin, serializers.HyperlinkedModelSerializer):
    created_by = serializers.HyperlinkedRelatedField(view_name='users:detail', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    updated_by = serializers.HyperlinkedRelatedField(view_name='users:detail', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.name', read_only=True)


class RolesCreateSerializer(RolesBaseSerializer):
    class Meta:
        fields = (
            'role_id',
            'name',
            'description',
            'created_by',
            'created_by_name',
            'created_date',
            'updated_by',
            'updated_by_name',
            'updated_date',
        )

        model = Roles


class RolesListSerializer(RolesBaseSerializer):
    url = HyperlinkedIdentityField(view_name='role_detail', lookup_field='role_id')

    class Meta:
        fields = (
            'role_id',
            'url',
            'name',
            'description',
        )
        model = Roles


class RolesDetailSerializer(RolesBaseSerializer):

    class Meta:
        fields = (
            'role_id',
            'name',
            'description',
            'created_by',
            'created_by_name',
            'created_date',
            'updated_by',
            'updated_by_name',
            'updated_date',
            'data_access',
            'menu_access',
            'dashboard_access',
            'report_access',
            'cases',
        )
        model = Roles
        extra_kwargs = {
            'name': {
                'validators': [
                    UniqueValidator(model.objects)
                ]
            }
        }


class RolesCopySerializer(RolesBaseSerializer):

    class Meta:
        fields = (
            'name',
        )
        model = Roles

        extra_kwargs = {
            'name': {
                "allow_blank": False,
                "required": True,
                'validators': [
                    UniqueValidator(model.objects.all())
                ]
            }
        }


class UserRoleSerializer(serializers.ModelSerializer):
    role = RolesDetailSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(queryset=Roles.objects, write_only=True, source='role')

    def create(self, validated_data):
        user_id = self.context['view'].kwargs['pk']
        already_exist = UserRole.objects.filter(
            user__user_id=user_id, role=validated_data['role']
        ).exists()

        if already_exist:
            raise exceptions.UserRoleAlreadyAssignedError()

        try:
            validated_data['user'] = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise UserNotFoundException()

        return super().create(validated_data)

    class Meta:
        fields = (
            'user_roles_id',
            'user_id',
            'role',
            'role_id'
        )

        model = UserRole


class RoleAttributeListSerializer(serializers.Serializer):
    label = serializers.CharField()
    name = serializers.CharField()
    is_parent = serializers.BooleanField()


class UsersAttachedToRoleListSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='user.user_id', read_only=True)
    url = serializers.HyperlinkedRelatedField(source='user_id', view_name='users:detail', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    is_temp_admin = serializers.BooleanField(source='user.is_temp_admin', read_only=True)
    status = OptionsMappingField(source='user.status', options=User.STATUS_CHOICES, read_only=True)

    class Meta:
        fields = (
            "user_roles_id",
            "url",
            "user_id",
            "name",
            "first_name",
            "last_name",
            "email",
            "user_name",
            "is_temp_admin",
            "status"
        )

        model = UserRole


class UsersNotAttachedToRoleList(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users:detail')
    status = OptionsMappingField(options=User.STATUS_CHOICES, read_only=True)

    class Meta:
        fields = (
            "url",
            "user_id",
            "name",
            "first_name",
            "last_name",
            "email",
            "user_name",
            "is_temp_admin",
            "status"
        )

        model = User
