import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.routing  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snap.settings')

# Normal HTTP traffic ke liye Django ka default ASGI
django_asgi_app = get_asgi_application()

# ProtocolTypeRouter decide karta hai ki request kahan jayegi
application = ProtocolTypeRouter({
    
    # 1. Agar request "http" hai, to 'urls.py' wale raste bhej do
    "http": django_asgi_app,
    
    # 2. Agar request "websocket" hai, to is raste bhej do
    "websocket": AuthMiddlewareStack(
        URLRouter(
            core.routing.websocket_urlpatterns
        )
    ),
})