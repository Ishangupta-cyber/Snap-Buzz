from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from core.models import FriendRequest

def stories_view(request):
    return render(request, "pages/stories.html")

@login_required
def camera(request):
    # Fetch user's friends to show in the "Send To" list
    friend_reqs = FriendRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status="accepted"
    )
    friends = []
    for req in friend_reqs:
        friends.append(req.to_user if req.from_user == request.user else req.from_user)

    return render(request, "pages/camera.html", {"friends": friends})

import json
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@login_required
def map_view(request):
    # Fetch user's friends to show on map
    friend_reqs = FriendRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status="accepted"
    )
    
    friends_data = []
    for req in friend_reqs:
        friend = req.to_user if req.from_user == request.user else req.from_user
        
        # Only include friends who have shared their location recently
        if friend.latitude and friend.longitude:
            # Check if location is recent (e.g., within last 24 hours)
            # For simplicity, we just check if it exists right now
            friends_data.append({
                "id": friend.id,
                "username": friend.username,
                "lat": friend.latitude,
                "lng": friend.longitude,
                "avatar": friend.avatar.url,
                "last_update": friend.last_location_update.strftime("%b %d, %I:%M %p") if friend.last_location_update else ""
            })

    # Pass as JSON string to the template
    friends_json = json.dumps(friends_data)
    
    return render(request, "pages/map.html", {"friends_json": friends_json})

@login_required
@require_http_methods(["POST"])
def update_location(request):
    try:
        data = json.loads(request.body)
        lat = data.get("lat")
        lng = data.get("lng")
        
        if lat is not None and lng is not None:
            request.user.latitude = float(lat)
            request.user.longitude = float(lng)
            request.user.last_location_update = timezone.now()
            request.user.save()
            return JsonResponse({"status": "success"})
            
        return JsonResponse({"status": "error", "message": "Invalid coordinates"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
