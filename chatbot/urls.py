from django.urls import path
from . import views

urlpatterns = [
    path("get-response/", views.chatbot_response, name="chatbot_response"),
]
