from django.urls import path
from . import views


urlpatterns=[
  path("",views.home,name="home"),
  path("register/",views.register_view,name="register-user"),
  path("login/",views.login_view,name="login-user"),
  path("logout/",views.logout_view,name="logout-user"),
  path("search/",views.search_view,name="search-users"),
  path("send-invite/<int:id>", views.send_invite, name="send-invite"),
  path("chat-details/<int:id>", views.chat_details_view, name="chat-details"),
  path("stories/", views.stories_view, name="stories"),
  path("send-message/<int:id>", views.send_message, name="send-message"),
  path("friend-requests/", views.friend_request_list, name="friend-requests"),
  path("accept-invite/<int:id>", views.accept_invite, name="accept-invite"),
  # path("send-snap/<int:id>", views.send_snap, name="send-snap"),
] 