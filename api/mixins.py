import json
import operator
import re
from functools import reduce

from django.db.models import Q, QuerySet
from rest_framework import serializers

from api import queryables, exceptions
from api.decorators import stored_property, stored_method
from db import get_customer_domain_from_request, get_user_info_from_request
from db.controller.models import Customer
from db.customer import models


class RequestArgMixin:
    arg_types = (int, bool, str, list)

    def get_argument(self, arg_name, arg_type=None, data=None, required=True, many=False):
        if data is None:
            data = self.request.data if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE') else self.request.query_params

        arg = data.get(arg_name)

        if not arg and not isinstance(arg, bool):
            if required:
                raise serializers.ValidationError('Argument "%s" is required' % arg_name)
            if many:
                return []

            return None

        if many:
            return self.parse_list(arg, arg_type, arg_name)

        if arg_type:
            arg = self.parse_argument(arg, arg_type, arg_name)

        return arg

    def parse_argument(self, arg, arg_type, arg_name):
        if arg_type not in self.arg_types:
            raise serializers.ValidationError('Argument type "%s" is not supported' % arg_type.__name__)

        if isinstance(arg, str):
            arg = getattr(self, 'parse_%s' % arg_type.__name__)(arg)

        if not isinstance(arg, arg_type):
            raise serializers.ValidationError('Argument "%s" should be a "%s" type' % (arg_name, arg_type.__name__))

        return arg

    def parse_list(self, arg_list, arg_type, arg_name):
        if isinstance(arg_list, str):
            try:
                arg_list = json.loads(arg_list)
            except ValueError:
                raise serializers.ValidationError('JSON parse error')

        if not isinstance(arg_list, list):
            raise serializers.ValidationError('Argument "%s" should be a "list" type' % arg_name)

        return [self.parse_argument(arg, arg_type, arg_name) for arg in arg_list]

    @staticmethod
    def parse_bool(value):
        return {'True': True, 'False': False}.get(value, value)

    @staticmethod
    def parse_int(value):
        return int(value) if value.isdigit() else value

    @staticmethod
    def parse_str(value):
        return value


class ManageUISimpleSearchMixin:
    # separator regex for split simple search
    separators_regex = '[ \-=~!@#$%^&*()_+\[\]{};:"|<,./<>?]'
    additional_search_fields = ()
    search_fields = (
        'created_by__user_id',
        'created_by__name',
        'updated_by__user_id',
        'updated_by__name',
    ) + additional_search_fields
    """
    Allows reuse of the view's search_fields array by removing id fields
    """
    def convert_search_to_simple_search(self, queryset, search_fields, id_fields) -> QuerySet:
        substring_search_fields = self._prepare_search_fields(self._search_fields_to_substring(search_fields, id_fields), id_fields)
        return self._simple_search(queryset, substring_search_fields, id_fields)

    def convert_search_to_split_simple_search(self, queryset, search_fields, id_fields, use_body_params=False) -> QuerySet:
        substring_search_fields = self._prepare_search_fields(self._search_fields_to_substring(search_fields, id_fields), id_fields)
        return self._split_simple_search(queryset, substring_search_fields, id_fields, use_body_params)

    def convert_body_search_to_simple_search(self, queryset, search_fields, id_fields) -> QuerySet:
        substring_search_fields = self._prepare_body_search_fields(self._search_fields_to_substring(search_fields, id_fields), id_fields)
        return self._simple_body_search(queryset, substring_search_fields, id_fields)

    def perform_simple_search(self, queryset, substring_search_fields, id_field) -> QuerySet:
        substring_search_fields = self._prepare_search_fields(substring_search_fields, (id_field, ))
        return self._simple_search(queryset, substring_search_fields, (id_field,))

    def _search_fields_to_substring(self, search_fields, id_fields):
        return [f + '__contains' for f in search_fields if f not in id_fields]

    def _prepare_search_fields(self, substring_search_fields, id_fields):
        search_fields = self.request.query_params.get('simple_search_fields')
        if search_fields:
            search_fields = search_fields.split(',')
            return self._search_fields_to_substring(search_fields, id_fields)
        return substring_search_fields

    def _simple_search(self, queryset, substring_search_fields, id_fields):
        search_term = self.request.query_params.get('simple_search')
        if search_term:
            predicates = [(field_name, search_term) for field_name in substring_search_fields]

            try:
                search_term = int(search_term)
                for field in id_fields:
                    predicates.append((field, search_term))
            except ValueError:
                pass

            q_list = [Q(x) for x in predicates]
            filter_clause = reduce(operator.or_, q_list)

            queryset = queryset.filter(filter_clause)

        return queryset

    def _prepare_body_search_fields(self, substring_search_fields, id_fields):
        search_fields = self.request.data.get('simple_search_fields')
        if search_fields:
            search_fields = search_fields.split(',')
            return self._search_fields_to_substring(search_fields, id_fields)
        return substring_search_fields

    def _simple_body_search(self, queryset, substring_search_fields, id_fields):
        search_term = self.request.data.get('simple_search')
        if search_term:
            predicates = [(field_name, search_term) for field_name in substring_search_fields]

            try:
                search_term = int(search_term)
                for field in id_fields:
                    predicates.append((field, search_term))
            except ValueError:
                pass

            q_list = [Q(x) for x in predicates]
            filter_clause = reduce(operator.or_, q_list)

            queryset = queryset.filter(filter_clause)

        return queryset

    def _search_terms_to_list(self, search_terms):
        return [search_term for search_term in re.split(self.separators_regex, search_terms.strip()) if search_term]

    def _split_simple_search(self, queryset, substring_search_fields, id_fields, use_body_params):
        if use_body_params:
            search_terms = self.request.data.get('simple_search')
        else:
            search_terms = self.request.query_params.get('simple_search')
        if search_terms:
            search_term_list = self._search_terms_to_list(search_terms)
            for search_term in search_term_list:
                predicates = [(field_name, search_term) for field_name in substring_search_fields]

                try:
                    search_term = int(search_term)
                    for field in id_fields:
                        predicates.append((field, search_term))
                except ValueError:
                    pass

                q_list = [Q(x) for x in predicates]
                filter_clause = reduce(operator.or_, q_list)

                queryset = queryset.filter(filter_clause)

        return queryset


class CustomerMixin(queryables.Queryable):

    @stored_property
    def customer_domain(self):
        # May be customer id if using HTTP_X_CUSTOMER_ID...
        return get_customer_domain_from_request(self.request)

    @stored_property
    def customer(self):
        try:
            # get_customer_domain_from_request can return the customer pk or domain
            int(self.customer_domain)
            return Customer.objects.using('controller').get(pk=self.customer_domain)
        except ValueError:
            return Customer.objects.using('controller').get(domain_name=self.customer_domain)

    @stored_property
    def username(self):
        username, _ = get_user_info_from_request(self.request)
        return username

    @stored_property
    def user(self):
        users = self.qs(models.User).filter(user_name=self.username)
        count = len(users)
        if count > 1:
            raise exceptions.DuplicateUsersException(self.username, count)

        return users.first()


class PermissionMixin(CustomerMixin):

    @stored_method
    def admin_role_check(self):
        # query that checks if a user has an admin role.
        return self.qs(models.UserRole).filter(
            role__name__in=(models.Roles.ADMIN_ROLE,),
            role__data_access=True,
            user_id=self.user.pk,
        ).exists()
