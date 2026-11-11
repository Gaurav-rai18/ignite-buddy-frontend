from django.urls import path
from .consumer import AssistantConsumer

websocket_urlpatterns = [path("ws/assistant/", AssistantConsumer.as_asgi())]
