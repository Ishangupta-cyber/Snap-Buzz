from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from core.models import FriendRequest, Conversation
from core.utils import are_friends


@login_required
def search_view(request):
    users = []
    friends = []
    unique_friends = set()
    pending = set()
    pending_requests = []

    search_username = request.GET.get("username")
    if search_username:
        users = get_user_model().objects.filter(username__icontains=search_username).exclude(id=request.user.id)

        queryset = FriendRequest.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        )
        friends = queryset.filter(status="accepted")
        pending_requests = queryset.filter(status="pending")

        for friend in friends:
            # IDs store karo (objects nahi) taaki template me `user.id in unique_friends` sahi kaam kare
            if friend.from_user_id == request.user.id:
                unique_friends.add(friend.to_user_id)
            else:
                unique_friends.add(friend.from_user_id)

        for req in pending_requests:
            if req.from_user_id == request.user.id:
                pending.add(req.to_user_id)
            else:
                pending.add(req.from_user_id)

    return render(request, "pages/search.html", {
        "search_username": search_username,
        "users": users,
        "unique_friends": unique_friends,
        "pending_requests": pending
    })


@require_http_methods(["POST"])
@login_required
def send_invite(request, id):
    if id == request.user.id:
        return JsonResponse({"status": "error", "message": "Cannot send request to yourself"})

    to_user = get_object_or_404(get_user_model(), id=id)

    if FriendRequest.objects.filter(Q(to_user=to_user, from_user=request.user) | Q(to_user=request.user, from_user=to_user)).exists():
        return JsonResponse({"status": "error", "message": "Request already exists"})
    else:
        FriendRequest.objects.create(to_user=to_user, from_user=request.user, status="pending")
        return JsonResponse({"status": "success", "message": "Request sent successfully"})


@login_required
@require_http_methods(["GET"])
def friend_request_list(request):
    friend_requests = FriendRequest.objects.filter(to_user=request.user, status="pending")
    return render(request, "pages/friend_requests.html", {"friend_requests": friend_requests})


@login_required
@require_http_methods(["POST"])
def accept_invite(request, id):
    friend_request = get_object_or_404(FriendRequest, id=id, to_user=request.user)

    if are_friends(request.user, friend_request.from_user):
        return JsonResponse({"status": "error", "message": "Already friends"})

    if friend_request.status == "pending":
        friend_request.status = "accepted"
        friend_request.save()

        user1, user2 = (request.user, friend_request.from_user) if request.user.id < friend_request.from_user.id else (friend_request.from_user, request.user)

        Conversation.objects.get_or_create(
            user1=user1, user2=user2,
            defaults={"last_message_preview": "You are now friends! Say hi! 👋"}
        )

        return JsonResponse({"status": "success", "message": "Request Accepted"})
    return JsonResponse({"status": "error", "message": "Invalid Request"})
