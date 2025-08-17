import numpy as np
import google.generativeai as genai
from django.conf import settings
from .tasks import embed_texts

def cosine_similarity(a, b):
    """
    Compute cosine similarity between two vectors
    """
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def embed_query(query: str):
    """
    Generate embedding for a query using Gemini
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    result = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )
    return result["embedding"]


def retrieve_relevant_chunks(query, document, top_k=5):
    query_embedding = embed_query(query)

    results = []
    for page in document.pages.all():
        for chunk, embedding in zip(page.text_chunks, page.chunk_embeddings):
            score = cosine_similarity(query_embedding, embedding)
            results.append({
                "text": chunk["text"],
                "start": chunk["start"],
                "end": chunk["end"],
                "page_number": chunk["page_number"],
                "score": score,
            })

    # sort by score
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results[:top_k]



def build_prompt(query: str, retrieved_chunks: list) -> str:
    """
    Build an augmented prompt with context for the LLM
    """
    context = "\n".join([
        f"(Page {c['page_number']}, chars {c['start']}-{c['end']}): {c['text']}"
        for c in retrieved_chunks
    ])

    prompt = f"""
    Use the following context to answer the question.
    Context:
    {context}

    Question: {query}

    Answer (with page + char ranges if relevant):
    """
    return prompt
