"""rehagoal_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path, include
from django.http.response import HttpResponseGone
from django.contrib import admin
from rest_framework.schemas import get_schema_view
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from rehagoal_server_app import views

schema_view = get_schema_view(title='RehaGoal API', version='2')

urlpatterns = [
    re_path(r'^$', views.index),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^api/v1/', HttpResponseGone),
    re_path(r'^api/v2/', include('rehagoal_server_app.urls')),
    re_path(r'^api/v2/schema/$', schema_view),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^api-token-auth/', obtain_jwt_token),
    re_path(r'^api-token-refresh/', refresh_jwt_token),
    re_path(r'^api-token-verify/', verify_jwt_token),
]
