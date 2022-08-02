from django.http import HttpResponse
from private_storage.views import PrivateStorageView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from re import fullmatch

from .models import ID_LENGTH


def index(request):
    return HttpResponse("")


# Download view, not on a per model level, but on a file level
class ContentFileDownloadView(APIView, PrivateStorageView):
    permission_classes = [IsAuthenticated]
    content_disposition = 'attachment'

    @staticmethod
    def can_access_file(private_file):
        # Permissions are managed by DRF permission_classes
        # Note that this is currently not on a per-object (Workflow) basis
        if fullmatch(r'[a-zA-Z0-9]{' + str(ID_LENGTH) + '}', private_file.relative_name) is None:
            return False
        return private_file.request.user.is_authenticated
