import PyPDF2
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Document, DocumentPage
from .serializers import DocumentUploadSerializer, DocumentResponseSerializer
from .tasks import process_pdf_async


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


