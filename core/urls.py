from django.urls import path
from . import views


urlpatterns=[
  path("",views.home,name="home"),
  path("register/",views.register_view,name="register-user"),
  path("login/",views.login_view,name="login-user"),
  path("logout/",views.logout_view,name="logout-user"),

  path("search/",views.search_view,name="search-users"), #search users page
  path("send-invite/<int:id>", views.send_invite, name="send-invite"), # send friend request

  path("stories/", views.stories_view, name="stories"),
  path("upload-story/", views.upload_story, name="upload-story"),
  
  path("chat-details/<int:id>", views.chat_details_view, name="chat-details"),
  path("send-message/<int:id>", views.send_message, name="send-message"),
  path("mark-snap-opened/<int:id>",views.mark_snap_opened,name="mark-snap-opened"),

  path("friend-requests/", views.friend_request_list, name="friend-requests"),
  path("accept-invite/<int:id>", views.accept_invite, name="accept-invite"),
  # path("send-snap/<int:id>", views.send_snap, name="send-snap"),
  path("camera/",views.camera,name="camera"),
  
  # Map Routes
  path("map/", views.map_view, name="map"),
  path("update-location/", views.update_location, name="update-location"),
] 