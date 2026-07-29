from django.urls import path
from . import consumers


websocket_urlpatterns = [
    # Yahan 'ws/chat/5/' jaisi request aayegi, to hum usko ChatConsumer ko de denge
    path('ws/chat/<int:friend_id>/', consumers.ChatConsumer.as_asgi()),
]