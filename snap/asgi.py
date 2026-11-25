import os

# Settings module SABSE PEHLE set karo, aur Django ko setup hone do
# (get_asgi_application) — uske BAAD hi app code (core.routing -> models) import karo.
# Warna standalone daphne (production) "Apps aren't loaded yet" error dega.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snap.settings")

from django.core.asgi import get_asgi_application  # noqa: E402

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

import core.routing  # noqa: E402

application = ProtocolTypeRouter({
    # Normal HTTP requests -> Django views
    "http": django_asgi_app,

    # WebSocket -> chat consumer. AllowedHostsOriginValidator doosri websites ko
    # aapke users ke naam pe socket kholne se rokta hai (ALLOWED_HOSTS se match karta hai).
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(core.routing.websocket_urlpatterns)
        )
    ),
})
