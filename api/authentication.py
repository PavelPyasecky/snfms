from datetime import datetime, timedelta
import pytz

from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from db import request_cfg, get_customer_domain_from_user


def set_request_cfg(request, auth):
    if auth and auth[0].is_authenticated:
        request_cfg.customer_domain_name, request_cfg.sf_username = get_customer_domain_from_user(auth[0])


class BasicAuthentication(authentication.BasicAuthentication):
    def authenticate(self, request):
        auth = super(BasicAuthentication, self).authenticate(request)
        set_request_cfg(request, auth)
        return auth


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate(self, request):
        auth = super(SessionAuthentication, self).authenticate(request)
        set_request_cfg(request, auth)
        return auth


class QueryStringTokenAuthentication(authentication.TokenAuthentication):
    def authenticate(self, request):
        token = request.query_params.get('token', [])
        if token:
            token_string = 'Token %s' % token
            request.META['HTTP_AUTHORIZATION'] = token_string

        auth = super(QueryStringTokenAuthentication, self).authenticate(request)
        set_request_cfg(request, auth)
        return auth


class ExpiringTokenAuthentication(authentication.TokenAuthentication):

    def authenticate(self, request):
        auth = super(ExpiringTokenAuthentication, self).authenticate(request)
        set_request_cfg(request, auth)
        return auth

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted')

        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=pytz.utc)

        if token.created < utc_now - timedelta(seconds=settings.AUTH_TOKEN_TTL_SECONDS):
            token.delete()
            raise AuthenticationFailed('Expired token')

        return token.user, token

