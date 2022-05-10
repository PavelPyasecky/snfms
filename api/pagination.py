from collections import OrderedDict

from django.core.paginator import Paginator
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination, _positive_int
from rest_framework.response import Response

from api.utils import is_csv_request


class CustomPageNumberPagination(PageNumberPagination):

    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        count = self.page.paginator.count
        permissionless_count = getattr(self, 'permissionless_count', count)
        return Response(OrderedDict([
            ('count', count),
            ('total_count', permissionless_count),
            ('page_size', self.get_page_size(self.request)),
            ('page_number', int(self.request.query_params.get(self.page_query_param, 1))),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]))


class QueryPaginator(Paginator):

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page

        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count

        self.object_list.limit(top-bottom, bottom)

        return self._get_page(self.object_list.select(), number, self)

    def _get_count(self):
        if self._count is None:
            self._count = self.object_list.count()

        return self._count

    count = property(_get_count)


class QueryPageNumberPagination(CustomPageNumberPagination):
    django_paginator_class = QueryPaginator


class CustomPaginationWithSinglePage(CustomPageNumberPagination):
    """
    This class is intended to overwrite get_page_size from rest_framework/pagination.py
    this lets us pass page_size=∞ to return all results on one single page
    """
    def get_page_size(self, request):
        if self.page_size_query_param:
            if is_csv_request(request):
                return None
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except KeyError:
                pass
            except ValueError:
                if request.query_params[self.page_size_query_param].lower() == "∞":  # %E2%88%9E
                    return None
        return self.page_size


class PaginatorWithNoCount(Paginator):
    @cached_property
    def count(self):
        """
        Returns the total number of objects, across all pages.
        In default implementation it calls count() to get the number of items in queryset.
        But this does not work with some kinds of tricky querysets, so changing it to len() call manually.
        """
        return len(self.object_list)


class PaginationWithNoCount(CustomPageNumberPagination):
    django_paginator_class = PaginatorWithNoCount
