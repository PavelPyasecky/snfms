from django.urls import path

from api.users import views

urlpatterns = [
    path('', views.UsersList.as_view(), name='list'),
    path('<int:pk>/', views.UsersDetail.as_view(), name='detail'),
]
