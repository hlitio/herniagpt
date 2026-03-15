from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.topic_list, name="topic_list"),
    path("new/", views.topic_create, name="topic_create"),
    path("topic/<slug:slug>/", views.topic_detail, name="topic_detail"),
    path("topic/<slug:slug>/edit/", views.topic_edit, name="topic_edit"),
    path("topic/<slug:slug>/chat/", views.start_topic_chat, name="start_topic_chat"),
]