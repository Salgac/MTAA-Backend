from django.urls import path

from .views import (
    RegisterView,
    Login,
    DemandListAPIView,
    DemandDetailAPIView,
    ItemDetailAPIView,
    ImageView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", Login.as_view(), name="login"),
    path("user/<filename>", ImageView.as_view(), name="user_image"),
    path("demand/", DemandListAPIView.as_view(), name="demand"),
    path("demand/<int:id>/", DemandDetailAPIView.as_view(), name="demand-detail"),
    path("item/<int:id>/", ItemDetailAPIView.as_view(), name="item-detail"),
]
