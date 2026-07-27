from django.contrib import admin
from .models import FriendRequest
from .models import Message,SnapUser,Conversation
# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(Message)
admin.site.register(SnapUser)
admin.site.register(Conversation)