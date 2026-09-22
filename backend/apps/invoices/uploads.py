import os

from django.conf import settings
from rest_framework import serializers

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
CONTENT_TYPE_BY_EXT = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def validate_upload(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Unsupported file type '{ext}'. Allowed formats: PDF, JPG, JPEG, PNG, TIFF."
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise serializers.ValidationError(
            f"File '{uploaded_file.name}' exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit."
        )
    return ext, CONTENT_TYPE_BY_EXT[ext]
