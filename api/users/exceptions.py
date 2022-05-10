from rest_framework import exceptions, status


class UserNotFoundException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User not found."


class UserDeactivationError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "Cannot deactivate user."


class UserActivationError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "Cannot activate user."


class UserPasswordResetError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class ForbiddenRole(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'May not alter user instances with this role.'
