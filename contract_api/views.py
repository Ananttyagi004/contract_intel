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


import google.generativeai as genai
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Document
from .serializers import RAGRequestSerializer, RAGResponseSerializer
from .utility_rag import retrieve_relevant_chunks, build_prompt


class DocumentQnAView(APIView):
    """
    POST API that answers questions based on a document (RAG style).
    """

    @extend_schema(
        request=RAGRequestSerializer,
        responses={200: RAGResponseSerializer},
        description="Answer a question based on a document using RAG. "
                    "Returns the answer and the page/char ranges (citations)."
        
    )
    def post(self, request, *args, **kwargs):
        serializer = RAGRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document = get_object_or_404(Document, id=data["document_id"])

        # Step 1: Retrieve top chunks
        retrieved_chunks = retrieve_relevant_chunks(data["query"], document, top_k=5)

        # Step 2: Build augmented prompt
        prompt = build_prompt(data["query"], retrieved_chunks)

        # Step 3: Generate answer
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Step 4: Prepare response payload
        response_payload = {
            "answer": response.text,
            "citations": [
                {"page": c["page_number"], "start": c["start"], "end": c["end"]}
                for c in retrieved_chunks
            ]
        }

        response_serializer = RAGResponseSerializer(response_payload)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import AuditRequestSerializer, AuditResponseSerializer, AuditFindingSerializer
from .models import Document
from .utility_audit import run_audit

class AuditView(APIView):
    @extend_schema(
        request=AuditRequestSerializer,
        responses=AuditResponseSerializer,
        description="Run automated contract audit to detect risky clauses"
    )
    def post(self, request):
        serializer = AuditRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            document = Document.objects.get(id=serializer.validated_data["document_id"])
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        findings = run_audit(document)

        response_serializer = AuditResponseSerializer({"findings": findings}, many=False)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


import json
import google.generativeai as genai
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from contract_api.models import Document
from contract_api.utility_rag import retrieve_relevant_chunks, build_prompt
from drf_spectacular.utils import OpenApiParameter

class DocumentQnAStreamView(APIView):
    """
    GET API that streams RAG answers using SSE.
    Example: /ask/stream?document_id=<uuid>&query=<text>
    """

    @extend_schema(
        parameters=[
        OpenApiParameter(name="document_id", description="UUID of the document", required=True, type=str),
        OpenApiParameter(name="query", description="User question to ask", required=True, type=str),
                        ],
        responses={200: None},
        description="Stream an answer (token by token) for a given document using RAG. "
                    "Events have JSON with type: token, citations, end, error."
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("query")
        document_id = request.query_params.get("document_id")
        if not query or not document_id:
            return StreamingHttpResponse(
                iter([f"data: {json.dumps({'type': 'error', 'message': 'Missing query or document_id'})}\n\n"]),
                content_type="text/event-stream"
            )

        document = get_object_or_404(Document, id=document_id)

        def event_stream():
            try:
                # Step 1: retrieve chunks
                retrieved_chunks = retrieve_relevant_chunks(query, document, top_k=5)

                # Step 2: build prompt
                prompt = build_prompt(query, retrieved_chunks)

                # Step 3: stream response from Gemini
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt, stream=True)

                for chunk in response:
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        token = chunk.candidates[0].content.parts[0].text
                        yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

                # Step 4: send citations at the end
                citations = [
                    {"page": c["page_number"], "start": c["start"], "end": c["end"]}
                    for c in retrieved_chunks
                ]
                yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"

                # Step 5: signal end of stream
                yield f"data: {json.dumps({'type': 'end'})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

import time
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import HealthzResponseSerializer, MetricsResponseSerializer


class HealthzView(APIView):
    """
    GET /healthz
    Simple health check endpoint.
    """

    @extend_schema(
        description="Health check endpoint. Returns 200 if API and DB are reachable.",
        responses={200: HealthzResponseSerializer},
    )
    def get(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"status": "unhealthy", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


REQUEST_COUNT = 0
START_TIME = time.time()


class MetricsView(APIView):
    """
    GET /metrics
    Exposes simple metrics like uptime and request count.
    """

    @extend_schema(
        description="Basic metrics endpoint (uptime, request count).",
        responses={200: MetricsResponseSerializer},
    )
    def get(self, request, *args, **kwargs):
        global REQUEST_COUNT
        REQUEST_COUNT += 1
        uptime = int(time.time() - START_TIME)

        metrics = {
            "uptime_seconds": uptime,
            "request_count": REQUEST_COUNT,
        }
        return Response(metrics, status=status.HTTP_200_OK)

