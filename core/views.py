from django.shortcuts import render,redirect
from . import forms
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login,logout,get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import FriendRequest
from django.shortcuts import get_object_or_404

# Create your views here.
@require_http_methods(["GET","POST"])
def register_view(request):
  if request.user.is_authenticated:
    print(request.user)
    return redirect("home")

  if request.method == "POST":
    form = forms.RegisterForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect("home")
  else:
    form = forms.RegisterForm()

  return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET","POST"])
def login_view(request):
  if request.user.is_authenticated:
    return redirect("home")

  form=forms.LoginForm(request,data=request.POST or None)
  if request.method=="POST":
    if form.is_valid():
      user=form.get_user()
      login(request,user)
      print(request.user)
      return redirect("home")
  return render(request,"accounts/login.html",{"form":form})

    

def logout_view(request):
  if request.user.is_authenticated:
    logout(request)
  return redirect("login-user")







@login_required
def home(request):
  print(request.user)
  friend_request=FriendRequest.objects.filter(
    Q(from_user=request.user) | Q(to_user=request.user)
  ).filter(status="accepted")

  friends=set()
  for friend in friend_request:
    if friend.to_user==request.user:
      friends.add(friend.from_user)
    else:
      friends.add(friend.to_user)

  return render(request,'pages/chat.html',{"friends":friends})




@login_required
def search_view(request) :
  users = []
  friends=[]
  unique_friends = set()
  pending=set()
  pending_requests = []

  search_username = request.GET.get("username")
  if search_username:

    users = (get_user_model().objects.filter(username__icontains=search_username).exclude(id=request.user.id))

    queryset = FriendRequest.objects. filter( 
      Q(from_user=request.user) | Q(to_user=request.user)
    )
    friends = queryset.filter(status="accepted")
    pending_requests = queryset.filter(status="pending")

    for friend in friends:
      if friend.from_user == request.user:
        unique_friends.add(friend.to_user)
      else:
        unique_friends.add(friend.from_user)

    for req in pending_requests:
      if request.user == req.from_user:
          pending.add(req.to_user.id)
      else:
          pending.add(req.from_user.id)

    

  return render(request, "pages/search.html", {"search_username": search_username, "users": users, "unique_friends": unique_friends,"pending_requests": pending})



@require_http_methods(["POST"])
@login_required
def send_invite(request, id):
  if id == request.user.id:
    return redirect("search-users")

  to_user = get_user_model().objects.get(id=id)
  # if FriendRequest.objects.filter(to_user=to_user, from_user=from_)user=request.user).exists():

  if FriendRequest.objects.filter(Q(to_user=to_user, from_user=request.user) | Q(to_user=request.user, from_user=to_user)).exists():
    return redirect("search-users")
  else:
    FriendRequest.objects.create(to_user=to_user, from_user=request.user, status="pending")
    return redirect("search-users")


@login_required
def chat_details_view(request, id):
    friend = get_object_or_404(get_user_model(), pk=id)
    return render(request, "pages/chat-details.html", {"friend": friend})

def accept_invite(request, id):
    friend_request = get_object_or_404(FriendRequest, id=id, to_user=request.user)
    if friend_request.status == "pending":
        friend_request.status = "accepted"
        friend_request.save()
    return redirect("home")


  


def stories_view(request):
    return render(request, "pages/stories.html")


 



#commit=FALSE matlb chenages abhi save nhi hue hai database mein