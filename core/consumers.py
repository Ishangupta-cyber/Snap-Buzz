import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .utils import are_friends


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Read-only realtime channel for a 1:1 chat.

    Messages are NOT created over the socket: the browser POSTs to /send-message/<id>,
    the view validates + saves + updates streaks, then broadcasts to this room.
    """

    async def connect(self):
        self.room_group_name = None
        self.user = self.scope["user"]
        friend_id = int(self.scope["url_route"]["kwargs"]["friend_id"])

        if not self.user.is_authenticated or friend_id == self.user.id:
            await self.close()
            return

        # Sirf dost hi ek doosre ke room me join kar sakte hain
        if not await self.check_friendship(friend_id):
            await self.close()
            return

        id1, id2 = sorted([self.user.id, friend_id])
        self.room_group_name = f"chat_{id1}_{id2}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Client se aane wale messages ignore karo — sending HTTP view se hoti hai
        pass

    # ---- Events broadcast via channel_layer.group_send ----

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event.get("message", ""),
            "sender_id": event["sender_id"],
            "message_id": event["message_id"],
            "image_url": event.get("image_url"),
        }))

    async def snap_opened(self, event):
        await self.send(text_data=json.dumps({
            "type": "snap_opened",
            "message_id": event["message_id"],
        }))

    @database_sync_to_async
    def check_friendship(self, friend_id):
        return are_friends(self.user.id, friend_id)
