from rest_framework import exceptions, views

from django.contrib.auth.models import User as UserAuth

from api.generics import NoCacheListCreateAPIView, NoCacheRetrieveUpdateAPIView
from api.mixins import RequestArgMixin, ManageUISimpleSearchMixin, PermissionMixin
from api.pagination import CustomPaginationWithSinglePage
from api.users.exceptions import ForbiddenRole
from api.users.filters import UsersFilterSet
from api.users.serializers import UsersListSerializer, UsersDetailSerializer
from db.customer.models import User, Roles
from tools import IsAuthenticatedAndAuthorized, CanAlterUsers
from tools.cors.decorators import allow_cors_methods, allow_cors


class AlterUserView(views.APIView, PermissionMixin):
    permission_classes = (CanAlterUsers,)


class UsersList(ManageUISimpleSearchMixin, NoCacheListCreateAPIView, PermissionMixin, RequestArgMixin):
    permission_classes = (IsAuthenticatedAndAuthorized,)
    serializer_class = UsersListSerializer
    pagination_class = CustomPaginationWithSinglePage
    filter_class = UsersFilterSet
    cors_methods = ['POST', 'GET', 'OPTIONS']

    DEFAULT_NEW_PASSWORD = '123456789'

    user_security_attributes = ('security.marketingadmin', 'security.crmadmin')

    ordering_fields = (
        'user_id',
        'first_name',
        'last_name',
        'email',
        'status',
    )

    search_fields = (
        'first_name',
        'last_name',
        'name',
        'user_name',
        'email',
        'status',
    )

    def _user_may_create_admin(self) -> bool:
        return self.admin_role_check()

    def create(self, request, *args, **kwargs):
        try:
            role_id = self.get_argument('default_role', required=False)
            if role_id:
                target_role = self.qs(Roles).get(role_id=role_id)
                if target_role.name == Roles.ADMIN_NAVIGATION and not self._user_may_create_admin():
                    raise ForbiddenRole(detail={'default_role': 'May not create user with this role.'})
        except Roles.DoesNotExist:
            raise exceptions.ValidationError({"default_role": "Role does not exist."})

        UserAuth.objects.create_user(f"{request.data['user_name']}@{self.customer_domain}", request.data['email'],
                                     self.DEFAULT_NEW_PASSWORD)

        return super().create(request, args, kwargs)

    @allow_cors('*')
    @allow_cors_methods(cors_methods)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.qs(User).exclude(status=0).only(
            'user_id', 'user_name', 'first_name', 'last_name', 'email', 'status', 'cookie_consent',
            'cookie_consent_date')

        filtered_queryset = self.convert_search_to_simple_search(
            queryset,
            self.search_fields,
            ('user_id',)
        )
        return filtered_queryset


class UsersDetail(NoCacheRetrieveUpdateAPIView, AlterUserView):
    serializer_class = UsersDetailSerializer

    def get_queryset(self):
        return self.qs(User)
