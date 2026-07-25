from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class FriendRequest(models.Model):
  from_user=models.ForeignKey(to=User,on_delete=models.CASCADE,related_name="sent_friend_requests")
  to_user=models.ForeignKey(to=User,on_delete=models.CASCADE,related_name="received_friend_requests")
  created_at=models.DateTimeField(auto_now_add=True)
  status=models.CharField(max_length=10,choices=[("pending","Pending"),("accepted","Accepted"),("rejected","Rejected")],default="pending")

  class Meta:
    unique_together=("from_user","to_user")

  def __str__(self):
    return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


class Message(models.Model):
  sender=models.ForeignKey(to=User,on_delete=models.CASCADE,related_name="sent_messages")
  receiver=models.ForeignKey(to=User,on_delete=models.CASCADE,related_name="received_messages")
  text_message=models.TextField()
  created_at=models.DateTimeField(auto_now_add=True)