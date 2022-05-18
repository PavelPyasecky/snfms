from django.urls import path

from api.messages import views

urlpatterns = [
    path('', views.MessageList.as_view(), name='list'),
    path('<int:pk>/', views.MessageDetail.as_view(), name='detail'),
]
