from rest_framework import permissions

from db import get_user_info_from_request
from tools.security.authorization import UserSecurityAttributesProvider


class IsAuthenticatedOrOptions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['OPTIONS']:
            return True
        return request.user and request.user.is_authenticated


class IsAuthenticatedAndAuthorized(IsAuthenticatedOrOptions):
    """
    This permissions class provides additional authorization checks to ensure that the user invoking the
    endpoint has the appropriate security attributes to do so.

    The relevant view is expected to define a member variable user_security_attributes as a tuple of strings
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and self._user_is_authorized(view)

    def _user_is_authorized(self, view):
        security_attributes = UserSecurityAttributesProvider(view.customer).get_security_settings(view.user)
        return set(view.user_security_attributes).intersection(security_attributes)


class CanAlterUsers(IsAuthenticatedOrOptions):
    """
    Allow admins to alter any user records. Allow non-admins to only alter their own user record.
    View must implement an admin_role_check() method or inherit from PermissionMixin.
    """
    def has_object_permission(self, request, view, obj):
        if view.admin_role_check():
            return True

        user_name, domain = get_user_info_from_request(request)

        return obj.user_name == user_name
