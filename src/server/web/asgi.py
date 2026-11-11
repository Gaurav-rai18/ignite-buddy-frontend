import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.web.settings")
from django.core.asgi import get_asgi_application

django_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from server import background
from server.realtime.routing import websocket_urlpatterns

background.start()
application = ProtocolTypeRouter({"http": django_app, "websocket": URLRouter(websocket_urlpatterns)})
