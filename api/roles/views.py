import distutils
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import DestroyAPIView, CreateAPIView
from rest_framework.response import Response

from api.generics import NoCacheListCreateAPIView, NoCacheRetrieveUpdateDeleteAPIView, NoCacheListAPIView
from api.mixins import CustomerMixin, ManageUISimpleSearchMixin, RequestArgMixin, PermissionMixin
from api.pagination import CustomPaginationWithSinglePage
from api.roles import serializers
from api.roles.filters import RolesFilterSet
from api.roles.serializers import RoleAttributeListSerializer, UsersAttachedToRoleListSerializer, \
    UsersNotAttachedToRoleList
from api.roles.services import validate_unique, RoleCopyService, RoleAttributesService
from db.customer.models import Roles, User, UserRole, RoleAttribute
from tools import IsAuthenticatedOrOptions
from tools.query import get_object_or_404_with_message


class RolesListCreateView(NoCacheListCreateAPIView,
                          CustomerMixin, ManageUISimpleSearchMixin, RequestArgMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    pagination_class = CustomPaginationWithSinglePage
    serializer_class = serializers.RolesListSerializer
    filter_class = RolesFilterSet

    filter_fields = (
        'role_id',
        'name',
        'description',
    )

    ordering_fields = (
        'role_id',
        'name',
        'description',
    )

    search_fields = (
        'role_id',
        'name',
        'description',
    )

    def get_queryset(self):
        return self.convert_search_to_simple_search(self.qs(Roles), self.search_fields, ('role_id',))

    def create(self, request, *args, **kwargs):
        name = self.get_argument(arg_name='name', arg_type=str, required=True)
        description = self.get_argument(arg_name='description', arg_type=str, required=True)
        user = self.user

        validate_unique(name, self.get_queryset())

        with transaction.atomic(using=self.customer_domain):
            role = self.qs(Roles).create(name=name, description=description, created_by=user, updated_by=user,
                                         updated_date=timezone.now(), created_date=timezone.now())

        serializer = serializers.RolesCreateSerializer(role, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RolesDetailView(NoCacheRetrieveUpdateDeleteAPIView, CustomerMixin, RequestArgMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = serializers.RolesDetailSerializer
    lookup_field = 'role_id'

    def get_queryset(self):
        return self.qs(Roles).select_related('created_by', 'updated_by')

    def log_access(self, data_access, menu_access, has_data_access_before, has_menu_access_before, role):
        if data_access and menu_access and data_access == menu_access and data_access != has_data_access_before and \
                menu_access != has_menu_access_before:
            attributes_log(self.user, self.customer_domain, role, ['data_access', 'menu_access'],
                           bool(distutils.util.strtobool(data_access)))
        else:
            if data_access and data_access != has_data_access_before:
                attributes_log(self.user, self.customer_domain, role, ['data_access'],
                               bool(distutils.util.strtobool(data_access)))
            if menu_access and menu_access != has_menu_access_before:
                attributes_log(self.user, self.customer_domain, role, ['menu_access'],
                               bool(distutils.util.strtobool(menu_access)))

    def patch(self, request, *args, **kwargs):
        role = self.get_object()
        has_data_access_before, has_menu_access_before = role.data_access, role.menu_access
        data_access = self.get_argument('data_access', str, required=False)
        menu_access = self.get_argument('menu_access', str, required=False)

        if menu_access not in (Roles.HAS_ACCESS_TRUE, Roles.HAS_ACCESS_FALSE, None) or data_access not in (
                Roles.HAS_ACCESS_TRUE, Roles.HAS_ACCESS_FALSE, None):
            return Response({'detail': 'Menu Access or Data Access can be only True or False'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.RolesDetailSerializer(role, data=request.data, partial=True,
                                                       context={'request': request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic(using=self.customer_domain):
            serializer.save()
            self.log_access(data_access, menu_access, has_data_access_before, has_menu_access_before, role)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        role_id = self.kwargs['role_id']
        role = get_object_or_404_with_message(
            {'detail': f'Role {role_id} does not exist!'})(self.qs(Roles), role_id=role_id)

        with transaction.atomic(using=self.customer_domain):
            self.qs(RoleAttribute).filter(role_id=role_id).delete()
            role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UsersAttachedToRoleList(NoCacheListCreateAPIView, DestroyAPIView, PermissionMixin,
                              RequestArgMixin, ManageUISimpleSearchMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = UsersAttachedToRoleListSerializer

    USER_ID_LIST_BODY_ARGUMENT = 'user_ids'

    search_fields = ('first_name', 'last_name', 'email',)

    ordering_fields = (
        "user_roles_id",
        "user_id",
        "name",
        "first_name",
        "last_name",
        "email",
        "user_name",
        "is_temp_admin",
        "status"
    )

    def _get_role(self):
        role_id = self.kwargs['role_id']
        return get_object_or_404_with_message(
            {'detail': f'Role {role_id} does not exist!'})(self.qs(Roles), role_id=role_id)

    def get_queryset(self):
        queryset = self._get_role().userrole_set.all().select_related('user')
        return self.convert_search_to_split_simple_search(queryset, ('user__first_name', 'user__last_name',
                                                                     'user__email'), ('user_id',))

    def handle_params(self, request, queryset):
        if request.data.get(self.USER_ID_LIST_BODY_ARGUMENT):
            user_ids = self.get_argument(self.USER_ID_LIST_BODY_ARGUMENT, int, required=True, many=True)
            updated_queryset = queryset.filter(user_id__in=user_ids)
        elif request.data.get('simple_search'):
            updated_queryset = self.convert_search_to_split_simple_search(
                queryset.filter(status=User.STATUS_ACTIVE), self.search_fields, ('user_id',), use_body_params=True)
        else:
            raise ValidationError("Incorrect params!")

        return updated_queryset

    def create(self, request, *args, **kwargs):
        role = self._get_role()

        if role.name in (Roles.ADMIN_NAVIGATION, Roles.ADMIN_ROLE) and not self.admin_role_check():
            raise PermissionDenied('Cannot assign admin role without admin authorization')

        updatable_users = self.qs(User).exclude(roles=role)

        # There are options:
        # 1) empty body of request - apply to all active users
        # 2) only user_ids param in the request - apply for corresponding users (active and inactive)
        # 3) only simple_search param in the request - all active users by filter criteria
        # if user_ids and simple_search presented simple_search will be ignored

        if not request.data:
            users_to_link = updatable_users.filter(status=User.STATUS_ACTIVE)
            msg = {"detail": "All active users have been attached to this role"}
        else:
            users_to_link = self.handle_params(request, updatable_users)
            msg = {"detail": "The role has been attached to these users"}

        with transaction.atomic(using=self.customer_domain):
            self.qs(UserRole).bulk_create([
                UserRole(role=role, user=user) for user in users_to_link
            ])
            user_history_log(self.user, self.customer_domain, role, users_to_link, True)

        return Response(msg, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        role = self._get_role()
        updatable_users = self.qs(User).filter(roles=role)

        # There are options:
        # 1) empty body of request - unlink from all active users
        # 2) only user_ids param in the request - unlink from corresponding users (active and inactive)
        # 3) only simple_search param in the request - all active users by filter criteria
        # if user_ids and simple_search presented simple_search will be ignored

        if not request.data:
            users_to_unlink = updatable_users.filter(status=User.STATUS_ACTIVE)
            msg = {"detail": "All active users have been unlinked from this role"}
        else:
            users_to_unlink = self.handle_params(request, updatable_users)
            msg = {"detail": "The role has been unlinked from these users"}

        with transaction.atomic(using=self.customer_domain):
            self.qs(UserRole).filter(role=role, user__in=users_to_unlink).delete()
            user_history_log(self.user, self.customer_domain, role, users_to_unlink, False)
        return Response({"detail": msg}, status=status.HTTP_200_OK)


class RolesAttributesView(NoCacheListCreateAPIView, DestroyAPIView, CustomerMixin, RequestArgMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = RoleAttributeListSerializer

    pagination_class = CustomPaginationWithSinglePage

    def _get_role(self):
        role_id = self.kwargs['role_id']
        return get_object_or_404_with_message(
            {'detail': f'Role {role_id} does not exist!'})(self.qs(Roles), role_id=role_id)

    def get_queryset(self):
        role = self._get_role()
        linked_attrs_values = self.get_attributes_dict(role.role_id, True)
        return [attribute for attribute in RoleAttributesService(self.customer).get_role_attributes()
                if attribute['name'] in linked_attrs_values]

    def get_attributes_dict(self, role_id, only_true_values=False):
        qs = self.qs(RoleAttribute).filter(role_id=role_id)
        if only_true_values:
            qs = qs.filter(name_value=RoleAttribute.NAME_VALUE_TRUE)
        return dict(qs.values_list('name', 'name_value'))

    def create(self, request, *args, **kwargs):
        attributes_to_add = self.get_argument('attributes', str, required=True, many=True)
        role = self._get_role()
        attributes_dict = self.get_attributes_dict(role.pk)

        with transaction.atomic(using=self.customer_domain):
            attributes_log(self.user, self.customer_domain, role,
                           (attr for attr in attributes_to_add if attr
                            not in attributes_dict or attributes_dict[attr] != RoleAttribute.NAME_VALUE_TRUE), True)

            self.qs(RoleAttribute).filter(name__in=attributes_to_add, role_id=role.pk).update(
                name_value=RoleAttribute.NAME_VALUE_TRUE)

            self.qs(RoleAttribute).bulk_create(
                (RoleAttribute(name=attr, name_value=RoleAttribute.NAME_VALUE_TRUE, role_id=role.pk)
                 for attr in attributes_to_add if attr not in attributes_dict))
        return Response({"detail": "Role attributes have been added"}, status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        attributes_to_delete = self.get_argument('attributes', str, required=True, many=True)
        role = self._get_role()
        attributes_dict = self.get_attributes_dict(role.pk)

        with transaction.atomic(using=self.customer_domain):
            attributes_log(self.user, self.customer_domain, role,
                           (attr for attr in attributes_to_delete if attr in
                            attributes_dict and attributes_dict[attr] == RoleAttribute.NAME_VALUE_TRUE), False)

            self.qs(RoleAttribute).filter(name__in=attributes_to_delete, role_id=role.pk).update(
                name_value=RoleAttribute.NAME_VALUE_FALSE)

            self.qs(RoleAttribute).bulk_create(
                (RoleAttribute(name=attr, name_value=RoleAttribute.NAME_VALUE_FALSE, role_id=role.pk)
                 for attr in attributes_to_delete if attr not in attributes_dict))
        return Response({"detail": "Role attributes have been removed"}, status.HTTP_200_OK)


class UsersNotAttachedToRoleList(ManageUISimpleSearchMixin, NoCacheListAPIView, CustomerMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = UsersNotAttachedToRoleList

    search_fields = ('first_name', 'last_name', 'email',)

    ordering_fields = (
        "user_id",
        "name",
        "first_name",
        "last_name",
        "email",
        "user_name",
        "is_temp_admin",
        "status"
    )

    def _get_role(self):
        role_id = self.kwargs['role_id']
        return get_object_or_404_with_message(
            {'detail': f'Role {role_id} does not exist!'})(self.qs(Roles), role_id=role_id)

    def get_queryset(self):
        role = self._get_role()
        qs = self.qs(User).filter(status=User.STATUS_ACTIVE).exclude(roles=role)
        return self.convert_search_to_split_simple_search(
            qs,
            self.search_fields,
            ('user_id',)
        )


class UserRoleCopy(CreateAPIView, CustomerMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = serializers.RolesCopySerializer

    copy_service_class = NotImplemented

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = get_object_or_404_with_message("Role does not exist.")(self.qs(Roles), pk=kwargs['role_id'])
        role_copy_service = RoleCopyService(self.customer_domain)
        copied_role = role_copy_service.copy_role(self.user, role, serializer.validated_data)

        serializer = serializers.RolesDetailSerializer(copied_role, context={'request': request, 'view': self})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        return self.qs(Roles)


class RolesAttributesUnlinkedView(NoCacheListAPIView, CustomerMixin):
    permission_classes = (IsAuthenticatedOrOptions,)
    serializer_class = RoleAttributeListSerializer

    pagination_class = CustomPaginationWithSinglePage

    def get_role_attributes(self):
        role = get_object_or_404_with_message("Role does not exist.")(self.qs(Roles), pk=self.kwargs['role_id'])
        return self.qs(RoleAttribute).filter(role_id=role.role_id)

    def get_queryset(self):
        linked_attrs_values = dict(self.get_role_attributes().values_list('name', 'name_value'))
        return [attribute for attribute in RoleAttributesService(self.customer).get_role_attributes()
                if not attribute['name'] in linked_attrs_values
                or not linked_attrs_values[attribute['name']] == RoleAttribute.NAME_VALUE_TRUE]
