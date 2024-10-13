import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers


class ImageBaseField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            header, base64_data = data.split(";base64,")
            extension = header.split("/")[-1]
            unique_name = f"{uuid.uuid4()}.{extension}"
            decoded_file = ContentFile(base64.b64decode(base64_data), name=unique_name)
            data = decoded_file
        return super().to_internal_value(data)
