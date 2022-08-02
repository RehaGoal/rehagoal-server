from django.urls import re_path, include
from rest_framework import routers

from . import api
from .views import ContentFileDownloadView
from .models import ID_LENGTH

router = routers.DefaultRouter()
router.register(r'users', api.RehagoalUserViewSet)
router.register(r'workflows', api.WorkflowViewSet)

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^files/(?P<path>[A-Za-z0-9]{' + str(ID_LENGTH) + '}|)$',
            ContentFileDownloadView.as_view(),
            name='serve_private_file')
]
