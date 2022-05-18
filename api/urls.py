from django.urls import path, include

from api.views import APIIndex

urlpatterns = [
    path('', APIIndex.as_view()),
    path('users/', include(('api.users.urls', 'api.users'), namespace='users')),
    path('messages/', include(('api.messages.urls', 'api.messages'), namespace='messages')),
    path('roles/', include(('api.roles.urls', 'api.roles'), namespace='roles')),
]
