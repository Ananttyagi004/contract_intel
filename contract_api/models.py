import uuid
from django.db import models


class Document(models.Model):
    """
    Stores uploaded PDF documents and their metadata
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=512)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    page_count = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Custom metadata fields")
    
    def __str__(self):
        return f"{self.filename} ({self.id})"


class DocumentPage(models.Model):
    """
    Stores text extracted from each page of a document
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="pages")
    page_number = models.IntegerField()
    text = models.TextField(help_text="Full text extracted from this page")
    
    # For vector search and RAG
    text_chunks = models.JSONField(default=list, help_text="Text chunks for vector search")
    chunk_embeddings = models.JSONField(default=list, help_text="Vector embeddings for chunks")
    
    
    def __str__(self):
        return f"Page {self.page_number} of {self.document.filename}"


class ExtractedFields(models.Model):
    """
    Stores structured fields extracted from contracts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='extracted_fields')
    
    # Parties information
    parties = models.JSONField(default=list, help_text="List of party information with name, type, address")
    
    # Key dates and terms
    effective_date = models.DateField(null=True, blank=True)
    term = models.CharField(max_length=255, null=True, blank=True, help_text="Contract term/duration")
    termination_date = models.DateField(null=True, blank=True)
    
    # Legal and financial terms
    governing_law = models.CharField(max_length=100, null=True, blank=True)
    payment_terms = models.TextField(null=True, blank=True)
    auto_renewal = models.BooleanField(null=True, blank=True)
    auto_renewal_notice_days = models.IntegerField(null=True, blank=True)
    
    # Risk-related fields
    confidentiality = models.TextField(null=True, blank=True)
    indemnity = models.TextField(null=True, blank=True)
    liability_cap_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    liability_cap_currency = models.CharField(max_length=3, null=True, blank=True, help_text="ISO currency code")
    
    # Signatories
    signatories = models.JSONField(default=list, help_text="List of signatories with name, title, date")
    
    # Additional extracted fields
    contract_type = models.CharField(max_length=100, null=True, blank=True)
    total_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    value_currency = models.CharField(max_length=3, null=True, blank=True)
    
    # Processing metadata
    extraction_confidence = models.FloatField(null=True, blank=True)
    extracted_at = models.DateTimeField(auto_now_add=True)
    extraction_model = models.CharField(max_length=100, blank=True)
    
    
    def __str__(self):
        return f"Extracted fields for {self.document.filename}"


class AuditFinding(models.Model):
    """
    Stores risk assessment findings from contract audits
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='audit_findings')
    
    # Finding details
    finding_type = models.CharField(max_length=100, help_text="Type of risk finding")
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Risk assessment
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    risk_score = models.FloatField(help_text="Risk score from 0-10")
    
    # Evidence and context - references specific pages and text spans
    evidence_text = models.TextField(help_text="Text evidence supporting the finding")
    page_number = models.IntegerField(help_text="Page where finding was detected")
    char_start = models.IntegerField(help_text="Start character position in page text")
    char_end = models.IntegerField(help_text="End character position in page text")
    
    # Recommendations
    recommendation = models.TextField(blank=True)
    compliance_impact = models.TextField(blank=True)
    
    # Metadata
    detected_at = models.DateTimeField(auto_now_add=True)
    detection_model = models.CharField(max_length=100, blank=True)

class APIMetrics(models.Model):
    """
    Tracks API usage metrics for monitoring
    """
    id = models.AutoField(primary_key=True)
    endpoint = models.CharField(max_length=100)
    method = models.CharField(max_length=10)
    
    # Counters
    request_count = models.BigIntegerField(default=0)
    error_count = models.BigIntegerField(default=0)
    
    # Timing
    avg_response_time_ms = models.FloatField(default=0.0)
    min_response_time_ms = models.FloatField(default=0.0)
    max_response_time_ms = models.FloatField(default=0.0)
    
    # Date tracking
    date = models.DateField(auto_now_add=True)
    last_request_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.method} {self.endpoint} on {self.date}"
