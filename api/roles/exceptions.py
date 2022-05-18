from rest_framework.exceptions import APIException


class UserRoleAlreadyAssignedError(APIException):
    status_code = 400
    default_code = "User already assigned to role."
