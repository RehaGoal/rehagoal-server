from rest_framework import serializers
from .models import MAX_FILE_SIZE
from django.template.defaultfilters import filesizeformat


def validate_workflow_content_size(content_file):
    if content_file.size > MAX_FILE_SIZE:
        raise serializers.ValidationError(f'Invalid file size. The file may not be larger than {filesizeformat(MAX_FILE_SIZE)}. Actual file size was {filesizeformat(content_file.size)}')
