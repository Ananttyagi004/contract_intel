from rest_framework import serializers
from .models import Document


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload requests"""
    files = serializers.ListField(
        child=serializers.FileField(
            max_length=512,
            allow_empty_file=False,
            use_url=False
        ),
        min_length=1,
        max_length=10
    )


class DocumentResponseSerializer(serializers.ModelSerializer):
    """Simple serializer for document responses"""
    
    class Meta:
        model = Document
        fields = ['id', 'filename', 'uploaded_at']
