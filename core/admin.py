from django.contrib import admin
from .models import FriendRequest
from .models import Message
from django.contrib.auth import get_user_model
# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(Message)