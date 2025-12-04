import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gemnar.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from chat.routing import websocket_urlpatterns  # noqa: E402
from chat.auth_middleware import HybridAuthMiddlewareStack  # noqa: E402


async def lifespan(scope, receive, send):
    if scope["type"] == "lifespan":
        message = await receive()
        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})


websocket_middleware = HybridAuthMiddlewareStack(URLRouter(websocket_urlpatterns))


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": websocket_middleware,
        "lifespan": lifespan,
    }
)
