# This code knows where to direct the login endpoint request
from django.urls import path
from .views import LoginAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="api-login"),
]
