"""
Errors module contains utility classes and helper functions for error handling
in snfms API.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class API404Error(APIException):
    """
    API404Error is an exception that should be thrown when 404 error is expected.
    """
    status_code = status.HTTP_404_NOT_FOUND


class API400Error(APIException):
    """
    API400Error is an exception that should be thrown when 400 error is expected.
    """
    status_code = status.HTTP_400_BAD_REQUEST
