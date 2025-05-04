from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.shortcuts import get_object_or_404
from core.services.document_processor import DocumentProcessor
from core.services.cnn_classifier import CNNClassifier
from core.models import Document, Classification, Notification
import os
import tempfile
import uuid
from django.conf import settings
import pytesseract
from pdf2image import convert_from_path
import docx2txt
from django.http import FileResponse
from django.core.cache import cache
from django.db import transaction
from core.utils import get_processing_lock, release_processing_lock

document_processor = DocumentProcessor()
cnn_classifier = CNNClassifier('ml_models/weights/cnn_model.h5')

class DocumentProcessView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        """Provide API documentation for this endpoint"""
        return Response({
            'message': 'This endpoint processes documents using OCR and classification',
            'usage': {
                'method': 'POST',
                'content_type': 'multipart/form-data',
                'parameters': {
                    'file': 'Document file to process',
                    'first_name': 'First name of the uploader',
                    'last_name': 'Last name of the uploader',
                    'email': 'Email of the uploader',
                    'purpose': 'Purpose of the document',
                    'description': 'Description of the document',
                    'enable_ocr': 'Whether to enable OCR processing'
                }
            }
        })

    def post(self, request, *args, **kwargs):
        temp_path = None
        lock_id = None
        
        try:
            # Input validation
            if 'file' not in request.FILES:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

            uploaded_file = request.FILES['file']
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            
            if file_extension not in allowed_extensions:
                return Response({
                    'error': f'Unsupported file type. Allowed types: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate unique IDs for processing
            processing_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Try to acquire processing lock
            if not get_processing_lock(processing_id, timeout=settings.PROCESSING_LOCK_TIMEOUT,
                                    max_retries=settings.PROCESSING_LOCK_MAX_RETRIES,
                                    retry_delay=settings.PROCESSING_LOCK_RETRY_DELAY):
                return Response({
                    "error": "System is busy processing another document. Please try again in a few moments."
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            lock_id = processing_id

            # Process document within transaction
            with transaction.atomic():
                try:
                    # Extract text using DocumentProcessor
                    extracted_text = document_processor.extract_text(temp_path)
                    
                    if not extracted_text or not extracted_text.strip():
                        raise ValueError("No text could be extracted from the document")

                    # Classify document using CNNClassifier
                    classifications = cnn_classifier.classify(extracted_text)
                    
                    if not classifications or classifications == ["unknown"]:
                        raise ValueError("Could not determine document type")

                    # Create document record
                    document = Document.objects.create(
                        file_id=document_id,
                        file_name=uploaded_file.name,
                        file_type=file_extension[1:],
                        file=uploaded_file,
                        extracted_text=extracted_text,
                        uploader_first_name=request.data.get('first_name', ''),
                        uploader_last_name=request.data.get('last_name', ''),
                        uploader_email=request.data.get('email', ''),
                        purpose=request.data.get('purpose', ''),
                        description=request.data.get('description', ''),
                        processed=True,
                        status='pending'
                    )

                    # Save classifications
                    for category in classifications:
                        Classification.objects.create(
                            document=document,
                            category=category,
                            confidence=1.0  # We'll implement actual confidence scores later
                        )

                    # Create notification
                    notification = Notification.objects.create(
                        document=document,
                        type='upload',
                        message=f"New document '{document.file_name}' uploaded by {document.uploader_first_name} {document.uploader_last_name}"
                    )

                    return Response({
                        'document_id': document.file_id,
                        'classifications': classifications,
                        'extracted_text': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
                        'file_type': file_extension[1:],
                        'message': 'Document processed and classified successfully'
                    }, status=status.HTTP_200_OK)

                except ValueError as ve:
                    # Rollback will happen automatically on ValueError
                    raise

        except ValueError as ve:
            return Response({
                'error': str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error processing document: {str(e)}")  # Log the error
            return Response({
                'error': 'An error occurred while processing the document. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clean up resources
            if lock_id:
                try:
                    release_processing_lock(lock_id)
                except Exception as e:
                    print(f"Error releasing lock: {str(e)}")
                    
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error removing temp file: {str(e)}")

class DocumentListView(APIView):
    def get(self, request):
        # Get filter parameters
        classification = request.query_params.get('classification', None)
        status_filter = request.query_params.get('status', None)
        
        # Start with all documents
        documents = Document.objects.all()
        
        # Filter by classification if specified
        if classification:
            documents = documents.filter(classifications__category=classification)

        # Filter by status if specified
        if status_filter:
            documents = documents.filter(status=status_filter)

        # Order by latest first
        documents = documents.order_by('-uploaded_at')

        return Response([{
            'id': doc.id,
            'file_name': doc.file_name,
            'file_type': doc.file_type,
            'uploaded_at': doc.uploaded_at,
            'classifications': [c.category for c in doc.classifications.all()],
            'description': doc.description,
            'uploader_name': f"{doc.uploader_first_name} {doc.uploader_last_name}".strip(),
            'status': doc.status
        } for doc in documents])

class DocumentStatusView(APIView):
    def put(self, request, document_id):
        try:
            document = get_object_or_404(Document, id=document_id)
            
            # Try to acquire lock with retries
            if not get_processing_lock(document.id, timeout=10, max_retries=3, retry_delay=0.5):
                return Response(
                    {"error": "Document is being processed. Please try again in a few moments."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            try:
                with transaction.atomic():
                    new_status = request.data.get('status')
                    
                    if new_status not in [choice[0] for choice in Document.STATUS_CHOICES]:
                        return Response(
                            {'error': 'Invalid status value'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    document.status = new_status
                    document.save()
                    
                    # Create status change notification
                    status_messages = {
                        'in_review': 'is now under review',
                        'approved': 'has been approved',
                        'rejected': 'has been rejected'
                    }
                    
                    if new_status in status_messages:
                        Notification.objects.create(
                            document=document,
                            type='status_change',
                            message=f"Document '{document.file_name}' {status_messages[new_status]}"
                        )
                    
                    return Response({
                        'id': document.id,
                        'file_name': document.file_name,
                        'status': document.status
                    })
            finally:
                release_processing_lock(document.id)
                
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NotificationView(APIView):
    def get(self, request):
        notifications = Notification.objects.all().order_by('-created_at')[:50]  # Get last 50 notifications
        return Response([{
            'id': notif.id,
            'type': notif.type,
            'message': notif.message,
            'created_at': notif.created_at,
            'is_read': notif.is_read,
            'document': {
                'id': notif.document.id,
                'file_name': notif.document.file_name,
                'status': notif.document.status
            }
        } for notif in notifications])
    
    def put(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})

class DocumentFileView(APIView):
    def get(self, request, document_id):
        try:
            document = get_object_or_404(Document, file_id=document_id)
            if not document.file:
                return Response({'error': 'No file available'}, status=status.HTTP_404_NOT_FOUND)
            
            return FileResponse(document.file, content_type=f'application/{document.file_type}')
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentDetailView(APIView):
    def get(self, request, document_id):
        try:
            document = get_object_or_404(Document, file_id=document_id)
            return Response({
                'id': document.file_id,
                'file_name': document.file_name,
                'file_type': document.file_type,
                'description': document.description,
                'status': document.status
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)