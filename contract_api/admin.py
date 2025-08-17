from django.contrib import admin
from .models import Document, DocumentPage, ExtractedFields, AuditFinding, APIMetrics


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'page_count', 'uploaded_at'
    ]
    list_filter = ['uploaded_at']
    search_fields = ['filename']
    readonly_fields = ['id', 'uploaded_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'filename', 'page_count', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('extracted_fields')


@admin.register(DocumentPage)
class DocumentPageAdmin(admin.ModelAdmin):
    list_display = [
        'document_name', 'page_number', 'text_preview', 'chunk_count'
    ]
    list_filter = ['page_number']
    search_fields = ['document__filename', 'text']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Page Information', {
            'fields': ('id', 'document', 'page_number')
        }),
        ('Content', {
            'fields': ('text', 'text_chunks', 'chunk_embeddings'),
            'classes': ('collapse',)
        }),
    )
    
    def document_name(self, obj):
        return obj.document.filename
    document_name.short_description = "Document"
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = "Text Preview"
    
    def chunk_count(self, obj):
        return len(obj.text_chunks) if obj.text_chunks else 0
    chunk_count.short_description = "Chunks"


@admin.register(ExtractedFields)
class ExtractedFieldsAdmin(admin.ModelAdmin):
    list_display = [
        'document_name', 'effective_date', 'auto_renewal', 
        'liability_cap_display', 'extraction_confidence', 'extracted_at'
    ]
    list_filter = ['auto_renewal', 'extracted_at', 'extraction_model']
    search_fields = ['document__filename']
    readonly_fields = ['id', 'extracted_at']
    
    fieldsets = (
        ('Document Reference', {
            'fields': ('id', 'document')
        }),
        ('Parties & Dates', {
            'fields': ('parties', 'effective_date', 'term', 'termination_date')
        }),
        ('Legal Terms', {
            'fields': ('governing_law', 'payment_terms', 'auto_renewal', 'auto_renewal_notice_days')
        }),
        ('Risk Fields', {
            'fields': ('confidentiality', 'indemnity', 'liability_cap_amount', 'liability_cap_currency')
        }),
        ('Additional Info', {
            'fields': ('signatories', 'contract_type', 'total_value', 'value_currency'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('extraction_confidence', 'extraction_model', 'extracted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_name(self, obj):
        return obj.document.filename
    document_name.short_description = "Document"
    
    def liability_cap_display(self, obj):
        if obj.liability_cap_amount and obj.liability_cap_currency:
            return f"{obj.liability_cap_amount} {obj.liability_cap_currency}"
        return "Not specified"
    liability_cap_display.short_description = "Liability Cap"


@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'document_name', 'severity', 'risk_score', 
        'finding_type', 'page_number', 'detected_at'
    ]
    list_filter = ['severity', 'finding_type', 'detected_at', 'detection_model']
    search_fields = ['title', 'description', 'document__filename']
    readonly_fields = ['id', 'detected_at']
    
    fieldsets = (
        ('Finding Details', {
            'fields': ('id', 'document', 'finding_type', 'title', 'description')
        }),
        ('Risk Assessment', {
            'fields': ('severity', 'risk_score', 'recommendation', 'compliance_impact')
        }),
        ('Evidence', {
            'fields': ('evidence_text', 'page_number', 'char_start', 'char_end'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('detection_model', 'detected_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_name(self, obj):
        return obj.document.filename
    document_name.short_description = "Document"


@admin.register(APIMetrics)
class APIMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'endpoint', 'method', 'date', 'request_count', 'error_count',
        'avg_response_time_ms', 'last_request_at'
    ]
    list_filter = ['date', 'method', 'endpoint']
    search_fields = ['endpoint']
    readonly_fields = ['id', 'date', 'last_request_at']
    
    fieldsets = (
        ('Endpoint Info', {
            'fields': ('id', 'endpoint', 'method', 'date')
        }),
        ('Counters', {
            'fields': ('request_count', 'error_count')
        }),
        ('Response Times', {
            'fields': ('avg_response_time_ms', 'min_response_time_ms', 'max_response_time_ms')
        }),
        ('Timestamps', {
            'fields': ('last_request_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Metrics are auto-generated
    
    def has_change_permission(self, request, obj=None):
        return False  # Metrics are read-only


# Customize admin site
admin.site.site_header = "Contract Intelligence API Administration"
admin.site.site_title = "Contract Intel Admin"
admin.site.index_title = "Welcome to Contract Intelligence API"
