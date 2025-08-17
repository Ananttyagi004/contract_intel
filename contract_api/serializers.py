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


class ExtractRequestSerializer(serializers.Serializer):
    document_id = serializers.UUIDField(help_text="UUID of the document to extract fields from")


class SignatorySerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Name of the signatory")
    title = serializers.CharField(help_text="Title/position of the signatory")
    date = serializers.DateField(help_text="Date of signature", required=False)


class ExtractedFieldsResponseSerializer(serializers.Serializer):
    parties = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of contract parties/companies"
    )
    effective_date = serializers.DateField(
        help_text="Effective date of the contract",
        required=False
    )
    term = serializers.CharField(
        help_text="Contract term/duration",
        required=False
    )
    governing_law = serializers.CharField(
        help_text="Governing law/jurisdiction",
        required=False
    )
    payment_terms = serializers.CharField(
        help_text="Payment terms and conditions",
        required=False
    )
    termination = serializers.DateField(
        help_text="Termination date",
        required=False
    )
    auto_renewal = serializers.BooleanField(
        help_text="Whether contract has auto-renewal",
        required=False
    )
    confidentiality = serializers.CharField(
        help_text="Confidentiality clauses",
        required=False
    )
    indemnity = serializers.CharField(
        help_text="Indemnification clauses",
        required=False
    )
    liability_cap = serializers.FloatField(
        help_text="Liability cap amount",
        required=False
    )
    liability_cap_currency = serializers.CharField(
        help_text="Currency of liability cap",
        required=False
    )
    signatories = serializers.ListField(
        child=SignatorySerializer(),
        help_text="List of signatories",
        required=False
    )
    contract_type = serializers.CharField(
        help_text="Type of contract",
        required=False
    )
    total_value = serializers.FloatField(
        help_text="Total contract value",
        required=False
    )
    value_currency = serializers.CharField(
        help_text="Currency of contract value",
        required=False
    )


class ExtractResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(help_text="Whether extraction was successful")
    message = serializers.CharField(help_text="Success/error message")
    document_id = serializers.UUIDField(help_text="ID of the processed document")
    extraction_method = serializers.CharField(help_text="Method used for extraction")
    extracted_fields = ExtractedFieldsResponseSerializer(help_text="Extracted contract fields")
