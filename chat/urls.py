from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),
    path("new/", views.conversation_create, name="new"),
    path("<int:pk>/", views.conversation_detail, name="detail"),
    path("<int:pk>/send/", views.send_message, name="send"),
    path("<int:pk>/send-stream/", views.send_message_stream, name="send_stream"),
    path("<int:pk>/rename/", views.conversation_rename, name="rename"),
    path("<int:pk>/delete/", views.conversation_delete, name="delete"),
]