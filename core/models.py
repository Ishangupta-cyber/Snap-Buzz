from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model

# Create your models here.


class SnapUser(AbstractUser) :
  avatar = models.ImageField(upload_to="avatar", default="snaps/default.jpg")

class FriendRequest(models.Model):
  from_user=models.ForeignKey(to=get_user_model(),on_delete=models.CASCADE,related_name="sent_friend_requests")
  to_user=models.ForeignKey(to=get_user_model(),on_delete=models.CASCADE,related_name="received_friend_requests")
  created_at=models.DateTimeField(auto_now_add=True)
  status=models.CharField(max_length=10,choices=[("pending","Pending"),("accepted","Accepted"),("rejected","Rejected")],default="pending")

  class Meta:
    unique_together=("from_user","to_user")

  def __str__(self):
    return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


class Message(models.Model):
  sender=models.ForeignKey(to=get_user_model(),on_delete=models.CASCADE,related_name="sent_messages")
  receiver=models.ForeignKey(to=get_user_model(),on_delete=models.CASCADE,related_name="received_messages")
  text_message=models.TextField(blank=True)
  image=models.ImageField(upload_to="snaps/",blank=True,null=True)
  created_at=models.DateTimeField(auto_now_add=True)




class Conversation(models.Model):
  user1=models.ForeignKey(to=get_user_model(),on_delete=models.CASCADE,related_name="conversations_as_user1")
  user2=models.ForeignKey(to=get_user_model(),on_delete=models.CASCADE,related_name="conversations_as_user2")
  last_message=models.ForeignKey(to=Message,on_delete=models.SET_NULL,related_name="+",null=True,blank=True)
  last_message_preview=models.CharField(blank=True,max_length=100)
  updated_at=models.DateTimeField(auto_now=True)
  created_at=models.DateTimeField(auto_now_add=True)

  class Meta:
    unique_together=("user1","user2")
    ordering=["-updated_at"]

  def __str__(self):
    return f"Chat: {self.user1.username} & {self.user2.username}"