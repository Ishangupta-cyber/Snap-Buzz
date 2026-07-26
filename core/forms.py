from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from django.contrib.auth.models import SnapUser
from .models import SnapUser

class RegisterForm(UserCreationForm) :
  class Meta:
    model = SnapUser
    fields = ["username", "password1", "password2","avatar"]

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      for field_name, field in self.fields.items():
          field.widget.attrs.update({
              'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition-all duration-300 placeholder-gray-400',
              'placeholder': f"Enter your {field.label.lower()}"
          })


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition-all duration-300 placeholder-gray-400',
                'placeholder': f"Enter your {field.label.lower()}"
            })