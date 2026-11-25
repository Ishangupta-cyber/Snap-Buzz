from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from django.core.cache import cache
from core import demo, forms

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        print(request.user)
        return redirect("home")

    if request.method == "POST":
        form = forms.RegisterForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = forms.RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = forms.LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            print(request.user)
            return redirect("home")
    return render(request, "accounts/login.html", {"form": form})


DEMO_LOGINS_PER_IP_PER_HOUR = 10


@require_http_methods(["POST"])
def demo_login_view(request):
    """'Try the demo' — log the visitor into a fresh, pre-filled guest account."""
    if request.user.is_authenticated:
        return redirect("home")

    # Basic abuse protection: each click creates an account, so cap it per IP
    key = f"demo-login:{request.META.get('REMOTE_ADDR', '')}"
    count = cache.get(key, 0)
    if count >= DEMO_LOGINS_PER_IP_PER_HOUR:
        form = forms.LoginForm(request)
        return render(request, "accounts/login.html", {
            "form": form,
            "demo_error": "Too many demo sessions from your network. Please try again in an hour.",
        }, status=429)
    cache.set(key, count + 1, 60 * 60)

    guest = demo.create_guest()
    login(request, guest, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("home")


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect("login-user")
