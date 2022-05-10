from django.urls import path

from api.messages import views

urlpatterns = [
    path('<int:user_id>/', views.MessageList.as_view(), name='message_list'),
]
