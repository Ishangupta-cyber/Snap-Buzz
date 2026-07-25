from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from django.contrib.auth.models import SnapUser
from .models import SnapUser

class RegisterForm(UserCreationForm) :
  class Meta:
    model = SnapUser
    fields = ["username", "password1", "password2","avatar"]


class LoginForm(AuthenticationForm):

  pass