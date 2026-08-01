from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from core.models import Message, Conversation
from core.utils import are_friends

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
    if not are_friends(request.user, get_object_or_404(get_user_model(), pk=id)):
        return redirect("home")
    
    receiver = get_object_or_404(get_user_model(), pk=id)
    content = request.POST.get("content", "")
    image = request.FILES.get("image")
    
    if content or image:
        msg = Message.objects.create(sender=request.user, receiver=receiver, text_message=content, image=image)

        if request.user.id < receiver.id:
            user1, user2 = request.user, receiver
            is_user1 = True
        else:
            user1, user2 = receiver, request.user
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

    return redirect("chat-details", id=id)


@require_http_methods(["POST"])
@login_required
def mark_snap_opened(request, id):
    msg = get_object_or_404(Message, id=id, receiver=request.user)
    if msg.image and not msg.is_opened:
        msg.is_opened = True
        msg.save()
        return JsonResponse({"status": "success", "message": "Snap marked as Opened"})
    return JsonResponse({"status": "already_opened", "message": "Snap is already opened"})
