import json
import operator
import re
from collections import OrderedDict
from functools import reduce
from http.client import responses
from math import ceil

from django.conf import settings
from django.db.models import Q, QuerySet
from querybuilder import query
from rest_framework import serializers
from rest_framework.response import Response

from api import queryables, exceptions
from api.decorators import stored_property, stored_method
from api.utils import is_csv_request
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


class LongListModelMixin:
    """
    This mixin is intended to overwrite "list" from rest_framework.mixins.ListModelMixin.
    For use in conjunction with sfapi.pagination.SalesfusionPaginationWithSinglePage
    to return the same structure response object with or without pagination.
    """
    def get_queryset_slices(self, queryset, limit, get_serializer=None):
        """
        Creates a generator for slicing a queryset up into chunks
        Pass in get_serializer method to return serialized data
        """
        for offset in range(ceil(queryset.count() / limit)):
            queryset_slice = queryset[offset * limit: offset * limit + limit]
            if get_serializer:
                queryset_slice = get_serializer(queryset_slice, many=True).data
            for qs_slice in queryset_slice:
                yield qs_slice

    def get_csv_response(self, queryset):
        """
        CSVs are generated with no page_size and may take longer than 2 minutes
        before we can return the response. This will cause nginx to kill the
        connection. Therefore, slice the queryset and use a StreamingHttpResponse.
        """
        queryset = self.get_queryset_slices(
            queryset,
            settings.SQL_SERVER_PARAMETER_LIMIT,
            self.get_serializer
        )
        response = responses.CSVStreamingHttpResponse(
            [field for field, value in self.get_serializer().fields.items() if not value.write_only], queryset
        )
        response['Content-Disposition'] = 'attachment; filename="SugarMarket.csv"'

        return response

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # This condition allows some custom views to return a list of dictionaries rather than an actual qs
        if isinstance(queryset, QuerySet):
            queryset = self.filter_queryset(queryset)

        # CSVs are generated with no page_size and may take longer than 2 minutes
        # before we can return the response. This will cause nginx to kill the
        # connection. Therefore, slice the queryset and use a StreamingHttpResponse.
        if is_csv_request(request):
            return self.get_csv_response(queryset)

        # SQL Server limits the amount of parameters sent per query. If we are using
        # prefetch_related and the number of rows returned could exceed this limit, batch
        # the queryset in slices.
        page_size = self.paginator.get_page_size(request)
        if ((not page_size or page_size > settings.SQL_SERVER_PARAMETER_LIMIT) and
                getattr(queryset, '_prefetch_related_lookups', None)):
            queryset = self.get_queryset_slices(queryset, settings.SQL_SERVER_PARAMETER_LIMIT)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        if isinstance(queryset, query.Query):
            queryset = queryset.select()

        serializer = self.get_serializer(queryset, many=True)
        count = len(serializer.data)
        permissionless_count = getattr(self.paginator, 'permissionless_count', count)
        return Response(OrderedDict([
            ('count', count),
            ('total_count', permissionless_count),
            ('page_size', count),
            ('page_number', self.get_page_number()),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', serializer.data),
        ]))

    def get_previous_link(self):
        return None

    def get_next_link(self):
        return None

    def get_page_number(self):
        return 1
