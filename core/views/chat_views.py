from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from core.models import Message, Conversation
from django.core.exceptions import ValidationError
from core.utils import are_friends, process_and_broadcast_message, clean_image
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@login_required
def home(request):
    conversations = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    chat_list = []
    for conv in conversations:
        friend = conv.user2 if request.user == conv.user1 else conv.user1
        chat_list.append({
            "friend": friend,
            "preview": conv.last_message_preview,
            "time": conv.updated_at,
            "streak_count": conv.streak_count
        })

    return render(request, 'pages/chat.html', {"chat_list": chat_list})


@login_required
def chat_details_view(request, id):
    friend = get_object_or_404(get_user_model(), pk=id)
    if not are_friends(request.user, friend):
        return redirect("home")
    
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by("created_at")

    messages = list(messages)

    # Delete text messages from friend once seen
    # received_messages = Message.objects.filter(receiver=request.user, sender=friend, text_message__isnull=False)
    # received_messages.delete()

    user1, user2 = (request.user, friend) if request.user.id < friend.id else (friend, request.user)
    conversation = Conversation.objects.filter(user1=user1, user2=user2).first()

    return render(request, "pages/chat-details.html", {"friend": friend, "messages": messages, "conversation": conversation})


@require_http_methods(["POST"])
@login_required
def send_message(request, id):
    receiver = get_object_or_404(get_user_model(), pk=id)
    if not are_friends(request.user, receiver):
        return JsonResponse({"status": "failed", "message": "You can only message friends"}, status=403)

    content = request.POST.get("content", "").strip()
    try:
        image = clean_image(request.FILES.get("image"))
    except ValidationError:
        return JsonResponse({"status": "failed", "message": "Please upload a valid image"}, status=400)

    if content or image:
        process_and_broadcast_message(request.user, receiver, content, image)
        return JsonResponse({"status": "success", "message": "Message sent!"})

    return JsonResponse({"status": "failed", "message": "Nothing to send"})


@require_http_methods(["POST"])
@login_required
def mark_snap_opened(request, id):
    msg = get_object_or_404(Message, id=id, receiver=request.user)
    if msg.image and not msg.is_opened:
        msg.is_opened = True
        msg.save()

        id1,id2=(request.user.id, msg.sender.id) if request.user.id<msg.sender.id else (msg.sender.id,request.user.id)
        conversation=Conversation.objects.filter(user1_id=id1,user2_id=id2).first()
        if conversation and conversation.last_message==msg:
            conversation.last_message_preview="📷 Opened a snap"
            conversation.save()
        room_name=f"chat_{id1}_{id2}"
        channel_layer=get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_name,
            {

                "type":"snap_opened",
                "message_id":msg.id

            }
        )


        return JsonResponse({"status": "success", "message": "Snap marked as Opened"})
    return JsonResponse({"status": "already_opened", "message": "Snap is already opened"})


# mark_snap_opened --> iska kaam hai ki jab user snap message pe click kare to ye function call ho jaye aur snap ko opened mark kare. Ye function snap message ko retrieve karega aur agar wo image hai aur abhi tak opened nahi hai to usko opened mark karega aur success response return karega. Agar snap already opened hai to already_opened response return karega. 

