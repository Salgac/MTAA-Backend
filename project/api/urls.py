from django.urls import path

from .views import (
    RegisterView,
    Login,
    DemandListAPIView,
    DemandDetailAPIView,
    ImageView,
    AvatarView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", Login.as_view(), name="login"),
    path("user/", ImageView.as_view(), name="user_image"),
    path("avatar/<filename>", AvatarView.as_view(), name="avatar"),
    path("demand/", DemandListAPIView.as_view(), name="demand"),
    path("demand/<int:id>/", DemandDetailAPIView.as_view(), name="demand-detail"),
]
