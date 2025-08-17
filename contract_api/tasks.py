import PyPDF2
import os
from celery import shared_task
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Document, DocumentPage


@shared_task(bind=True)
def process_pdf_async(self, document_id, file_path):
    """
    Async task to process PDF and extract text
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Check if file exists
        if not default_storage.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Open and process PDF
        with default_storage.open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Process each page
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Create text chunks (simple sentence-based chunking)
                    chunks = create_text_chunks(text)
                    
                    # Create DocumentPage record
                    DocumentPage.objects.create(
                        document=document,
                        page_number=page_num + 1,  # 1-indexed
                        text=text,
                        text_chunks=chunks,
                        chunk_embeddings=[]  # Initialize empty embeddings
                    )
                    
                    # Update task progress
                    progress = int((page_num + 1) / len(pdf_reader.pages) * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': page_num + 1, 'total': len(pdf_reader.pages), 'progress': progress}
                    )
                    
                except Exception as e:
                    # Log page error but continue
                    print(f"Error processing page {page_num + 1}: {str(e)}")
                    continue
            
            # Mark task as complete
            self.update_state(
                state='SUCCESS',
                meta={'message': f'Successfully processed {len(pdf_reader.pages)} pages'}
            )
            
    except Exception as e:
        # Mark task as failed
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


def create_text_chunks(text, max_chunk_size=1000):
    """
    Create text chunks for vector search
    """
    if not text or len(text) <= max_chunk_size:
        return [text] if text else []
    
    # Simple sentence splitting
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Add period back if it was removed
        if not sentence.endswith('.'):
            sentence += '.'
        
        # If adding this sentence would exceed chunk size, save current chunk
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
