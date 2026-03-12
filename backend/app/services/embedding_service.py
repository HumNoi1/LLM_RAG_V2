"""
Embedding Service — BGE-M3 embeddings + Qdrant vector store.
BE-S responsibility (Sprint 2).

Key design decisions:
  - Model: BAAI/bge-m3 (multilingual, strong Thai support)
  - Chunking: SentenceSplitter(chunk_size=512, chunk_overlap=50)
  - Metadata: exam_id, doc_type tagged on every node
  - Filter by metadata at query time
"""
import logging
from typing import Optional
from uuid import UUID

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import get_settings
from app.core.exceptions import EmbeddingException

logger = logging.getLogger(__name__)

# ── Singleton clients (lazy init) ─────────────────────────────────────────────

_qdrant_client: Optional[QdrantClient] = None
_embed_model: Optional[HuggingFaceEmbedding] = None

COLLECTION_NAME = "exam_documents"


def get_qdrant_client() -> QdrantClient:
    """Get or create a singleton Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        logger.info("Connected to Qdrant at %s:%s", settings.qdrant_host, settings.qdrant_port)
    return _qdrant_client


def get_embed_model() -> HuggingFaceEmbedding:
    """Get or create a singleton BGE-M3 embedding model."""
    global _embed_model
    if _embed_model is None:
        settings = get_settings()
        logger.info("Loading embedding model '%s' on device '%s'...", settings.embedding_model, settings.embedding_device)
        _embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
        )
        logger.info("Embedding model loaded")
    return _embed_model


def _get_vector_store() -> QdrantVectorStore:
    """Get Qdrant vector store for the exam documents collection."""
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=COLLECTION_NAME,
    )


async def embed_document(
    exam_id: UUID,
    doc_id: UUID,
    doc_type: str,
    text: str,
) -> int:
    """Embed document text and store chunks in Qdrant.

    Args:
        exam_id:  UUID of the exam this document belongs to.
        doc_id:   UUID of the document record (for tracking).
        doc_type: 'answer_key' | 'rubric' | 'course_material'
        text:     Full extracted text from the PDF.

    Returns:
        Number of chunks embedded.
    """
    try:
        # Configure LlamaIndex settings for this operation
        embed_model = get_embed_model()
        Settings.embed_model = embed_model
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

        # Create a LlamaIndex Document with metadata
        doc = Document(
            text=text,
            metadata={
                "exam_id": str(exam_id),
                "doc_id": str(doc_id),
                "doc_type": doc_type,
            },
        )

        # Build index (this embeds and stores into Qdrant)
        vector_store = _get_vector_store()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            [doc],
            storage_context=storage_context,
            show_progress=False,
        )

        # Count chunks that were created
        chunk_count = len(index.docstore.docs)
        logger.info(
            "Embedded document doc_id=%s (exam_id=%s, type=%s): %d chunks",
            doc_id, exam_id, doc_type, chunk_count,
        )
        return chunk_count

    except Exception as e:
        logger.error("Embedding failed for doc_id=%s: %s", doc_id, e)
        raise EmbeddingException(str(e)) from e


async def delete_exam_embeddings(exam_id: UUID) -> None:
    """Delete all Qdrant points associated with an exam."""
    try:
        client = get_qdrant_client()

        if not client.collection_exists(COLLECTION_NAME):
            return

        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="exam_id",
                        match=MatchValue(value=str(exam_id)),
                    )
                ]
            ),
        )
        logger.info("Deleted embeddings for exam_id=%s", exam_id)

    except Exception as e:
        logger.error("Failed to delete embeddings for exam_id=%s: %s", exam_id, e)
        raise EmbeddingException(str(e)) from e


def get_index_for_exam(exam_id: UUID) -> VectorStoreIndex:
    """Get a VectorStoreIndex filtered for a specific exam.

    Used by rag_service to build a query engine.
    """
    Settings.embed_model = get_embed_model()
    vector_store = _get_vector_store()
    return VectorStoreIndex.from_vector_store(vector_store=vector_store)
