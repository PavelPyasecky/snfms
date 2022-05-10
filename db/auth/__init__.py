from datetime import datetime

from django.contrib.auth import logout as auth_logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


class UnsafeSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class ObtainAuthTokenCSRF(ObtainAuthToken):
    authentication_classes = (UnsafeSessionAuthentication,)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        session_key = getattr(request.session, 'session_key')

        if session_key:
            auth_logout(request)

        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        if not created:
            token.created = datetime.utcnow()
            token.save()

        payload = {
            'token': token.key,
            'csrf_token': get_token(request)
        }
        resp = Response(payload)
        resp['Cache-Control'] = 'no-cache'
        if request.GET.get("auth_headers", False):
            resp['X-CSRF'] = payload.get("csrf_token", "")
            resp['X-Auth-Token'] = payload.get("token", "")
        return resp

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ObtainAuthTokenCSRF, self).dispatch(*args, **kwargs)
