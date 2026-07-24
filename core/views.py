from django.shortcuts import render,redirect
from . import forms
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login,logout

# Create your views here.
@require_http_methods(["GET","POST"])
def register_view(request):
  if request.user.isauthenticated:
    return redirect("home")

  form = forms.RegisterForm(request.POST)
  if request.method == "POST":
    if form.is_valid():
      user=form.save()
      login(request,user)
      return redirect("home")
  return render(request,"accounts/register.html",{"form":form})


@require_http_methods(["GET","POST"])
def login_view(request):
  if request.user.isauthenticated:
    return redirect("home")

  form=forms.LoginForm(request.POST or None)
  if request.method=="POST":
    if form.is_valid():
      user=form.get_user()
      login(request,user)
      return redirect("home")

    
# @require_http_methods(["GET","POST"])
def logout_view(request):
  if request.user.is_authenticated:
    logout(request)


def home(request):
  return render(request,'pages/chat.html')


#commit=FALSE matlb chenages abhi save nhi hue hai database mein