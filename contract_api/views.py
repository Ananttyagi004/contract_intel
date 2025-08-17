import PyPDF2
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Document, DocumentPage
from .serializers import (
    DocumentUploadSerializer, 
    DocumentResponseSerializer,
    ExtractRequestSerializer,
    ExtractResponseSerializer
)
from .tasks import process_pdf_async
from .extraction_service import ContractExtractionService
from datetime import datetime


class IngestAPIView(APIView):
    """
    API View for uploading and processing PDF documents
    """
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        request=DocumentUploadSerializer,  
        responses={201: DocumentResponseSerializer},             
    )
    def post(self, request):
        """
        Handle PDF upload and processing
        """
        try:
            # Validate request
            serializer = DocumentUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            files = serializer.validated_data['files']
            
            # Process files
            documents = []
            for uploaded_file in files:
                # Create document record first
                document = Document.objects.create(
                    filename=uploaded_file.name,
                    metadata={}  # Initialize empty, will be populated with extracted metadata
                )
                
                # Save file
                file_path = f"contracts/{document.id}/{uploaded_file.name}"
                default_storage.save(file_path, uploaded_file)
                
                # Extract basic metadata from PDF
                try:
                    uploaded_file.seek(0)
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    
                    # Extract PDF metadata
                    pdf_metadata = {
                        'page_count': len(pdf_reader.pages),
                        'file_size': uploaded_file.size,
                        'pdf_info': pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {},
                        'filename': uploaded_file.name,
                        'content_type': uploaded_file.content_type
                    }
                    
                    # Update document with extracted metadata
                    document.metadata = pdf_metadata
                    document.page_count = len(pdf_reader.pages)
                    document.save()
                    
                    # Queue async task for text extraction
                    process_pdf_async.delay(document.id, file_path)
                    
                except Exception as e:
                    # If metadata extraction fails, still save document but mark error
                    document.metadata = {
                        'error': str(e),
                        'filename': uploaded_file.name
                    }
                    document.save()
                
                documents.append(document)
            
            # Return document IDs immediately (processing continues in background)
            response_data = DocumentResponseSerializer(documents, many=True).data
            return Response({
                'success': True,
                'message': 'Files uploaded successfully. Text extraction in progress.',
                'document_ids': [doc['id'] for doc in response_data],
                'documents': response_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExtractAPIView(APIView):
    """
    API View for extracting contract fields from processed documents using pure LLM approach
    """
    
    @extend_schema(
        request=ExtractRequestSerializer,
        responses={200: ExtractResponseSerializer},             
    )
    def post(self, request):
        """
        Extract contract fields from a document using Gemini Flash LLM
        """
        try:
            # Validate request
            serializer = ExtractRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            document_id = serializer.validated_data['document_id']
            
            # Check if document exists and has been processed
            try:
                document = Document.objects.get(id=document_id)
            except Document.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Document not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if document has been processed (has pages)
            if not document.pages.exists():
                return Response({
                    'success': False,
                    'error': 'Document not yet processed. Please wait for text extraction to complete.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract fields using pure LLM service
            extraction_service = ContractExtractionService()
            result = extraction_service.extract_fields(document_id)
            
            if result['success']:
                # Save extracted fields to database
                self._save_extracted_fields(document, result['extracted_fields'])
                
                return Response({
                    'success': True,
                    'message': 'Contract fields extracted successfully using Gemini Flash LLM',
                    'document_id': str(document_id),
                    'extraction_method': result['extraction_method'],
                    'extracted_fields': result['extracted_fields']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _save_extracted_fields(self, document, extracted_fields):
        """Save extracted fields to ExtractedFields model"""
        from .models import ExtractedFields
        
        # Convert date strings to date objects
        effective_date = None
        termination_date = None
        
        if extracted_fields.get('effective_date'):
            try:
                effective_date = datetime.strptime(extracted_fields['effective_date'], '%Y-%m-%d').date()
            except:
                pass
        
        if extracted_fields.get('termination'):
            try:
                termination_date = datetime.strptime(extracted_fields['termination'], '%Y-%m-%d').date()
            except:
                pass
        
        # Create or update ExtractedFields
        extracted_obj, created = ExtractedFields.objects.get_or_create(
            document=document,
            defaults={
                'parties': extracted_fields.get('parties', []),
                'effective_date': effective_date,
                'term': extracted_fields.get('term'),
                'termination_date': termination_date,
                'governing_law': extracted_fields.get('governing_law'),
                'payment_terms': extracted_fields.get('payment_terms'),
                'auto_renewal': extracted_fields.get('auto_renewal'),
                'confidentiality': extracted_fields.get('confidentiality'),
                'indemnity': extracted_fields.get('indemnity'),
                'liability_cap_amount': extracted_fields.get('liability_cap'),
                'liability_cap_currency': extracted_fields.get('liability_cap_currency'),
                'signatories': extracted_fields.get('signatories', []),
                'contract_type': extracted_fields.get('contract_type'),
                'total_value': extracted_fields.get('total_value'),
                'value_currency': extracted_fields.get('value_currency'),
                'extraction_model': 'pure_llm_gemini_flash'
            }
        )
        
        if not created:
            # Update existing record
            extracted_obj.parties = extracted_fields.get('parties', [])
            extracted_obj.effective_date = effective_date
            extracted_obj.term = extracted_fields.get('term')
            extracted_obj.termination_date = termination_date
            extracted_obj.governing_law = extracted_fields.get('governing_law')
            extracted_obj.payment_terms = extracted_fields.get('payment_terms')
            extracted_obj.auto_renewal = extracted_fields.get('auto_renewal')
            extracted_obj.confidentiality = extracted_fields.get('confidentiality')
            extracted_obj.indemnity = extracted_fields.get('indemnity')
            extracted_obj.liability_cap_amount = extracted_fields.get('liability_cap')
            extracted_obj.liability_cap_currency = extracted_fields.get('liability_cap_currency')
            extracted_obj.signatories = extracted_fields.get('signatories', [])
            extracted_obj.contract_type = extracted_fields.get('contract_type')
            extracted_obj.total_value = extracted_fields.get('total_value')
            extracted_obj.value_currency = extracted_fields.get('value_currency')
            extracted_obj.extraction_model = 'pure_llm_gemini_flash'
            extracted_obj.save()


