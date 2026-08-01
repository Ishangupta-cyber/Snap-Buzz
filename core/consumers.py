
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.friend_id=self.scope["url_route"]["kwargs"]["friend_id"]

        self.user=self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return 

        id1, id2 = sorted([self.user.id, int(self.friend_id)])
        self.room_group_name = f'chat_{id1}_{id2}'
        # 2. User ko is room me bitha do (Channel Layer / Post Office ki madad se)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name # (Ye current user ki personal connection id hoti hai)
        )
        await self.accept()

    # 2. DISCONNECT FUNCTION
    async def disconnect(self, close_code):
        # Jab user page band karta hai, toh usko us Room (group) se hata do
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    # 3. RECEIVE FUNCTION
    async def receive(self, text_data):
        # Jab javascript se user message type karke bhejega, wo yahan aayega
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        
        if message.strip():
            # 1. Message ko Database me save karo
            msg_obj = await self.save_message(self.user.id, self.friend_id, message)
            
            # 2. Is naye message ko room me baithe sabhi logon (Aap aur dost) ki taraf feink do (Broadcast)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',  # Ye batata hai ki kaunsa function chalana hai
                    'message': message,
                    'sender_id': self.user.id,
                    'message_id': msg_obj.id,
                }
            )


    # 4. CHAT_MESSAGE FUNCTION
    async def chat_message(self, event):
        # Ye function tab call hota hai jab 'group_send' ne message room me feinka tha
        # Ye bas us message ko pakadta hai aur Javascript walo ko de deta hai dikhane ke liye
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'message_id': event['message_id'],
        }))


    # ---- HELPER FUNCTION ----
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message_text):
        # Kyunki Channels async hai, database call direct nahi kar sakte. 
        # Ise isliye '@database_sync_to_async' ke andar rakhte hain.
        User = get_user_model()
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        
        msg = Message.objects.create(sender=sender, receiver=receiver, text_message=message_text)
        return msg

    async def snap_opened(self, event):
        message_id = event["message_id"]
        await self.send(text_data=json.dumps({
            "type": "snap_opened",
            "message_id": message_id
        }))

    async def chat_message(self, event):
        # View ya doosri jagah se jo group_send hua, wo 'event' ban kar yahan aata hai
        await self.send(text_data=json.dumps({
            'message': event.get('message', ''),
            'sender_id': event['sender_id'],
            'message_id': event['message_id'],
           
            'image_url': event.get('image_url')
        }))