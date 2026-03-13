from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),
    path("new/", views.conversation_create, name="new"),
    path("<int:pk>/", views.conversation_detail, name="detail"),
    path("<int:pk>/send/", views.send_message, name="send"),
]