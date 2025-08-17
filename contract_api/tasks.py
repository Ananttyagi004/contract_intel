import PyPDF2
import os
import google.generativeai as genai
from celery import shared_task
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Document, DocumentPage
import openai

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
                    chunks = create_text_chunks(text,page_num+1)
                    
                    # Generate embeddings using Gemini
                    embeddings = embed_texts(chunks)
                    
                    # Create DocumentPage record
                    DocumentPage.objects.create(
                        document=document,
                        page_number=page_num + 1,  # 1-indexed
                        text=text,
                        text_chunks=chunks,
                        chunk_embeddings=embeddings
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


def create_text_chunks(text,page_number, max_chunk_size=1000):
    """
    Create text chunks for vector search.
    Always returns list of dicts: {text, start, end}
    """
    if not text:
        return []

    # If somehow text is already a list of strings (bad input), wrap into dicts
    if isinstance(text, list):
        return [
            {"text": str(t), "start": 0, "end": len(str(t)), "page_number": page_number}
            for t in text
        ]

    # Normal case: text is a string
    if len(text) <= max_chunk_size:
        return [{"text": text.strip(), "start": 0, "end": len(text)}]

    sentences = text.replace("\n", " ").split(". ")
    chunks = []
    current_chunk = ""
    start = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if not sentence.endswith("."):
            sentence += "."

        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            end = start + len(current_chunk)
            chunks.append({"text": current_chunk.strip(), "start": start, "end": end, "page_number": page_number})
            start = end
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence

    if current_chunk:
        end = start + len(current_chunk)
        chunks.append({"text": current_chunk.strip(), "start": start, "end": end, "page_number": page_number})

    return chunks



import google.generativeai as genai
from django.conf import settings

def embed_texts(text_chunks):
    """
    Generate embeddings using Gemini's embedding model.
    Expects a list of dicts like:
    [{"text": "...", "start": 0, "end": 100}, ...]
    """
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            print("Warning: GEMINI_API_KEY not set. Returning empty embeddings.")
            return []
        
        # Configure Gemini client
        genai.configure(api_key=api_key)

        embeddings = []
        for chunk in text_chunks:
            # ✅ Always extract the actual text
            text = ""
            if isinstance(chunk, dict):
                text = chunk.get("text", "")
            elif isinstance(chunk, str):
                text = chunk
            else:
                text = str(chunk)

            if text.strip():
                try:
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=text,
                        task_type="retrieval_document"
                    )
                    embedding = result["embedding"]
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Error generating embedding for chunk: {str(e)}")
                    embeddings.append([0.0] * 768)  # fallback
            else:
                embeddings.append([0.0] * 768)

        return embeddings

    except Exception as e:
        print(f"Error in embed_texts: {str(e)}")
        return []







