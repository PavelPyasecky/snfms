from typing import Optional

from rest_framework.exceptions import APIException, status


class GenericFailureException(APIException):

    def __init__(self, default_detail, status_code=400, **kwargs):
        self.default_detail = default_detail
        self.status_code = status_code
        super(GenericFailureException, self).__init__(**kwargs)


class NothingToDoException(APIException):

    def __init__(self, **kwargs):
        default_detail = "No work can be found to do at this time"
        super(NothingToDoException, self).__init__(default_detail, **kwargs)


class DuplicateUsersException(GenericFailureException):

    def __init__(self, user_name, count, **kwargs):
        default_detail = "Duplicate users found for username %s -- currently there are %s" % (user_name, count)
        super(DuplicateUsersException, self).__init__(default_detail, **kwargs)


class ValueOutOfRangeException(ValueError):
    pass


class ValueOutOfRangeAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, status_code: Optional[int] = None, detail: Optional[str] = None):
        self.default_detail = detail or 'Value out of range'

        if status_code:
            self.status_code = status_code

        super().__init__()


class UnacceptableValueException(ValueError):
    pass
