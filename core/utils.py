from .models import FriendRequest, Message, Conversation
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def are_friends(user1, user2):
    return FriendRequest.objects.filter(
        Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1),
        status="accepted"
    ).exists()

def process_and_broadcast_message(sender, receiver, content, image):
    """
    Handles message creation, conversation/streak updates, and WebSocket broadcasting.
    """
    msg = Message.objects.create(sender=sender, receiver=receiver, text_message=content, image=image)

    if sender.id < receiver.id:
        user1, user2 = sender, receiver
        is_user1 = True
    else:
        user1, user2 = receiver, sender
        is_user1 = False
    
    preview = "📷 Sent a snap" if image else content[:50]

    conv, created = Conversation.objects.get_or_create(
        user1=user1, user2=user2,
        defaults={"last_message": msg, "last_message_preview": preview}
    )

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    if conv.streak_updated_at and conv.streak_updated_at < yesterday:
        conv.streak_count = 0

    if image:
        if is_user1:
            conv.last_snap_user1 = timezone.now()
        else:
            conv.last_snap_user2 = timezone.now()

    if conv.last_snap_user1 and conv.last_snap_user2:
        if conv.last_snap_user1.date() == today and conv.last_snap_user2.date() == today:
            if conv.streak_updated_at != today:
                conv.streak_count += 1
                conv.streak_updated_at = today

    conv.last_message = msg
    conv.last_message_preview = preview
    conv.save()

    room_name = f"chat_{user1.id}_{user2.id}"
    image_url = msg.image.url if msg.image else None

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room_name,
        {
            "type": "chat_message",
            "message": content,
            "sender_id": sender.id,
            "message_id": msg.id,
            "image_url": image_url
        }
    )
