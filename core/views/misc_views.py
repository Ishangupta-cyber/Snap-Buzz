from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from core.models import FriendRequest, Story
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse

@login_required
def stories_view(request):
    # Fetch stories from the last 24 hours
    time_threshold = timezone.now() - timedelta(hours=24)
    recent_stories = Story.objects.filter(created_at__gte=time_threshold)
    
    # Group stories by user so we can display one circle per user
    user_stories = {}
    for story in recent_stories:
        if story.user not in user_stories:
            user_stories[story.user] = []
        user_stories[story.user].append(story)
        
    return render(request, "pages/stories.html", {"user_stories": user_stories})

from django.http import JsonResponse

@login_required
def upload_story(request):
    if request.method == "POST" and request.FILES.get("image"):
        Story.objects.create(
            user=request.user,
            image=request.FILES["image"]
        )
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

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
    # Khali panna (blank slate) for map
    return render(request, "pages/map.html")

import os
from django.conf import settings

@login_required
def spotlight_view(request):
    stories_dir = os.path.join(settings.MEDIA_ROOT, 'stories')
    videos = []
    if os.path.exists(stories_dir):
        videos = [f for f in os.listdir(stories_dir) if f.endswith('.mp4')]
    
    # Return full URL paths
    video_urls = [f"{settings.MEDIA_URL}stories/{v}" for v in videos]
    
    return render(request, "pages/spotlight.html", {"videos": video_urls})


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

           
            return JsonResponse({"status": "success", "message": "Location Backend me Save Ho Gayi!"})
            
        return JsonResponse({"status": "error", "message": "Coordinates nahi mile"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
