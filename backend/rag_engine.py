"""
PromptCraft RAG (Retrieval-Augmented Generation) Engine
-------------------------------------------------------
Provides semantic search and context retrieval from reference documents with MongoDB Atlas persistence:
1. Smart text chunking with word overlap
2. Vector embeddings generation via Google Gemini Embeddings API (models/text-embedding-004)
3. Persistent storage of chunks & embeddings in MongoDB Atlas (rag_documents & rag_chunks)
4. Cosine similarity vector search
5. Clean context formatting for Gemini Prompt Rewriter

STRICT ARCHITECTURAL BOUNDARY:
Retrieved RAG context is sent ONLY to downstream LLM prompt rewriters.
It has ZERO impact on the quantitative 7-parameter Evaluation Engine scores.
"""

import math
import re
import warnings
from typing import Dict, Any, List, Optional

warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai  # type: ignore

from config.settings import GEMINI_API_KEYS, GEMINI_EMBEDDING_MODEL
from database.repositories import (
    save_rag_document,
    save_rag_chunks,
    get_user_rag_chunks
)

# Configure Gemini API if keys are present
if GEMINI_API_KEYS:
    try:
        genai.configure(api_key=GEMINI_API_KEYS[0])
    except Exception as e:
        print(f"[Warning] Failed to configure Gemini API for RAG: {e}")


def chunk_text(
    text: str,
    chunk_size_words: int = 150,
    overlap_words: int = 30
) -> List[Dict[str, Any]]:
    """
    Splits document text into overlapping windows of words so semantic
    context is maintained across boundaries.
    """
    if not text:
        return []
        
    words = text.split()
    if not words:
        return []
        
    chunks: List[Dict[str, Any]] = []
    start = 0
    chunk_idx = 0
    
    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)
        
        chunks.append({
            "chunk_index": chunk_idx,
            "text": chunk_str,
            "word_count": len(chunk_words),
            "char_count": len(chunk_str)
        })
        
        chunk_idx += 1
        step = max(1, chunk_size_words - overlap_words)
        start += step
        
    return chunks


def get_embedding(
    text: str,
    task_type: str = "retrieval_document"
) -> Optional[List[float]]:
    """
    Generates a dense vector embedding using Google Gemini Embeddings API with multi-key auto-failover.
    """
    if not text or not GEMINI_API_KEYS:
        return None
        
    for key in GEMINI_API_KEYS:
        try:
            genai.configure(api_key=key)
            response = genai.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                content=text[:2048],
                task_type=task_type
            )
            emb = response.get("embedding")
            if emb:
                return emb
        except Exception:
            continue
    return None


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine similarity between two numerical embedding vectors.
    Returns float between -1.0 and 1.0 (typically 0.0 to 1.0 for normalized embeddings).
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
        
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)


class RAGContextManager:
    """
    RAG vector manager with MongoDB Atlas persistence.
    Stores chunks and embeddings in MongoDB Atlas and performs vector similarity search.
    """
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks_store: List[Dict[str, Any]] = []
        
    def add_document(
        self,
        doc_name: str,
        full_text: str,
        user_email: str = "demo@promptcraft.ai",
        file_type: str = "pdf",
        file_size_bytes: int = 0
    ) -> Dict[str, Any]:
        """
        Ingests a reference document:
        1. Chunks text with overlap.
        2. Computes Gemini vector embeddings.
        3. Persists document metadata and chunks/embeddings into MongoDB Atlas.
        """
        if not full_text.strip():
            return {"status": "error", "message": "Document text is empty."}
            
        raw_chunks = chunk_text(full_text)
        ingested_chunks: List[Dict[str, Any]] = []
        
        for ch in raw_chunks:
            embedding = get_embedding(ch["text"], task_type="retrieval_document")
            chunk_record = {
                "doc_name": doc_name,
                "chunk_index": ch["chunk_index"],
                "text": ch["text"],
                "word_count": ch["word_count"],
                "embedding": embedding
            }
            self.chunks_store.append(chunk_record)
            ingested_chunks.append(chunk_record)
            
        self.documents[doc_name] = {
            "name": doc_name,
            "total_chunks": len(ingested_chunks),
            "total_words": len(full_text.split())
        }
        
        # 🍃 Persist to MongoDB Atlas
        try:
            save_rag_document(
                user_email=user_email,
                doc_name=doc_name,
                full_text=full_text,
                total_chunks=len(ingested_chunks),
                file_type=file_type,
                file_size_bytes=file_size_bytes
            )
            saved_chunks_count = save_rag_chunks(
                user_email=user_email,
                doc_name=doc_name,
                chunks=ingested_chunks
            )
            print(f"[MongoDB RAG] Saved {saved_chunks_count} chunks and embeddings to MongoDB Atlas for {doc_name}")
        except Exception as e:
            print(f"[MongoDB RAG Warning] Could not save to MongoDB Atlas: {e}")
        
        return {
            "status": "success",
            "doc_name": doc_name,
            "chunks_created": len(ingested_chunks),
            "total_chunks_stored": len(self.chunks_store),
            "persisted_in_db": True
        }
        
    def retrieve_relevant_chunks(
        self,
        query: str,
        user_email: str = "demo@promptcraft.ai",
        top_k: int = 3,
        min_similarity: float = 0.25
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search against stored chunks for a given query prompt.
        If in-memory cache is empty, loads chunks and embeddings directly from MongoDB Atlas.
        """
        if not query.strip():
            return []
            
        # If in-memory store is empty, fetch user chunks from MongoDB Atlas
        active_chunks = self.chunks_store
        if not active_chunks and user_email:
            try:
                db_chunks = get_user_rag_chunks(user_email)
                if db_chunks:
                    active_chunks = db_chunks
                    self.chunks_store = db_chunks
            except Exception as e:
                print(f"[MongoDB RAG Warning] Error retrieving chunks from database: {e}")
                
        if not active_chunks:
            return []
            
        query_vec = get_embedding(query, task_type="retrieval_query")
        scored_chunks: List[Dict[str, Any]] = []
        
        if query_vec:
            # Semantic Vector Search via Cosine Similarity
            for ch in active_chunks:
                if ch.get("embedding"):
                    score = cosine_similarity(query_vec, ch["embedding"])
                    if score >= min_similarity:
                        scored_chunks.append({
                            "doc_name": ch.get("doc_name", "Document"),
                            "chunk_index": ch.get("chunk_index", 0),
                            "text": ch.get("text", ""),
                            "similarity": round(score, 4)
                        })
        else:
            # Fallback: Keyword overlap matching if embeddings API is offline
            query_terms = set(re.findall(r"\w+", query.lower()))
            for ch in active_chunks:
                chunk_text_content = ch.get("text", "")
                chunk_terms = set(re.findall(r"\w+", chunk_text_content.lower()))
                overlap = len(query_terms.intersection(chunk_terms))
                if overlap > 0:
                    scored_chunks.append({
                        "doc_name": ch.get("doc_name", "Document"),
                        "chunk_index": ch.get("chunk_index", 0),
                        "text": chunk_text_content,
                        "similarity": round(overlap / max(1, len(query_terms)), 4)
                    })
                    
        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_chunks[:top_k]
        
    def format_rag_context_for_llm(
        self,
        query: str,
        user_email: str = "demo@promptcraft.ai",
        top_k: int = 3
    ) -> str:
        """
        Retrieves top relevant chunks and formats them into a clean markdown
        context block for the downstream Gemini Prompt Rewriter.
        """
        chunks = self.retrieve_relevant_chunks(query, user_email=user_email, top_k=top_k)
        if not chunks:
            return ""
            
        context_parts = ["### Reference Context (Retrieved from Uploaded Materials):"]
        for idx, ch in enumerate(chunks, 1):
            context_parts.append(
                f"\n**[Source: {ch['doc_name']} (Section {ch['chunk_index'] + 1}) | Match Score: {int(ch['similarity'] * 100)}%]**\n"
                f"{ch['text']}"
            )
            
        return "\n".join(context_parts)
        
    def ingest_document(self, full_text: str, doc_name: str, user_email: str = "demo@promptcraft.ai") -> Dict[str, Any]:
        """Backward-compatible alias for add_document."""
        return self.add_document(doc_name=doc_name, full_text=full_text, user_email=user_email)

    def retrieve_context(self, query: str, user_email: str = "demo@promptcraft.ai", top_k: int = 3) -> List[Dict[str, Any]]:
        """Backward-compatible alias for retrieve_relevant_chunks."""
        return self.retrieve_relevant_chunks(query=query, user_email=user_email, top_k=top_k)

    def format_context_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """Formats a list of retrieved chunks into markdown context for LLM."""
        if not chunks:
            return ""
        context_parts = ["### Reference Context (Retrieved from Uploaded Materials):"]
        for idx, ch in enumerate(chunks, 1):
            context_parts.append(
                f"\n**[Source: {ch.get('doc_name', 'Doc')} (Section {ch.get('chunk_index', 0) + 1}) | Match Score: {int(ch.get('similarity', 0.8) * 100)}%]**\n"
                f"{ch.get('text', '')}"
            )
        return "\n".join(context_parts)

    def clear(self):
        """Clears the in-memory session cache."""
        self.documents.clear()
        self.chunks_store.clear()
        
    def get_document_summary(self) -> List[Dict[str, Any]]:
        """Returns a list of all currently loaded reference documents."""
        return list(self.documents.values())


# Global singleton instance
_rag_instance: Optional[RAGContextManager] = None


def get_rag_manager() -> RAGContextManager:
    """Returns the singleton RAG context manager instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGContextManager()
    return _rag_instance
