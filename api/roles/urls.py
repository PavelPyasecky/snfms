from django.urls import path

from api.roles import views

urlpatterns = [
    path('', views.RolesListCreateView.as_view(), name='role_list_create'),
    path(r'^(?P<role_id>[0-9]+)/$', views.RolesDetailView.as_view(), name='role_detail'),
    path(r'^(?P<role_id>[0-9]+)/clone/$', views.UserRoleCopy.as_view(), name='role_copy'),
    path(r'^(?P<role_id>[0-9]+)/users/$', views.UsersAttachedToRoleList.as_view(), name='users_attached_to_role_list'),
    path(r'^(?P<role_id>[0-9]+)/users/unlinked/$', views.UsersNotAttachedToRoleList.as_view(),
        name='users_not_attached_to_role_list'),
    path(r'^(?P<role_id>[0-9]+)/attributes/$', views.RolesAttributesView.as_view(), name='role_attributes'),
    path(r'^(?P<role_id>[0-9]+)/attributes/unlinked/$', views.RolesAttributesUnlinkedView.as_view(),
        name='role_attributes_unlinked'),
]
