"""
Query module contains helpful utility functions
for constructing and running queries using Django ORM.
"""

from typing import Union, Callable

from django.shortcuts import _get_queryset

from tools.errors import API404Error


def get_object_or_404_with_message(message: Union[str, dict]) -> Callable:
    """
    Customized version of Django's get_object_or_404. This method creates a callable get_object_or_404 with
    customized error message.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Like with QuerySet.get(), MultipleObjectsReturned is raised if more than
    one object is found.

    Example of usage:
    get_object_or_404_with_message("Object does not exist.")(ModelName.objects, pk=5)
    """

    def get_object_or_404(klass, *args, **kwargs):
        queryset = _get_queryset(klass)
        if not hasattr(queryset, 'get'):
            klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
            raise ValueError(
                "First argument to get_object_or_404() must be a Model, Manager, "
                "or QuerySet, not '%s'." % klass__name
            )
        try:
            return queryset.get(*args, **kwargs)
        except queryset.model.DoesNotExist:
            raise API404Error(message)

    return get_object_or_404
