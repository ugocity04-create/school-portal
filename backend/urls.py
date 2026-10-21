"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include as _include, path as _path
from django.contrib import admin as _admin

urlpatterns = [_path("api/",
_include("portal.urls"))]

urlpatterns += [_path("admin/", _admin.site.urls)]

from django.conf import settings as _settings
from django.conf.urls.static import static as _static

urlpatterns += _static(_settings.MEDIA_URL, document_root=_settings.MEDIA_ROOT)

# ===================== Show the React site at the home address =====================
from portal import views_spa as _spa
from django.urls import re_path as _re_path
from django.views.static import serve as _serve

urlpatterns += [
    _path("favicon.svg", _spa.favicon),
    _path("", _spa.index),
    # profile pictures (on the free host they reset when the site restarts)
    _re_path(r"^media/(?P<path>.*)$", _serve, {"document_root": _settings.MEDIA_ROOT}),
]
