"""
Embedding Service — BGE-M3 embeddings + Qdrant vector store.
BE-S responsibility (Sprint 2).
Sprint 4: Performance tuning — configurable batch size, chunk params, Qdrant query params.

Key design decisions:
  - Model: BAAI/bge-m3 (multilingual, strong Thai support)
  - Chunking: SentenceSplitter with configurable chunk_size / chunk_overlap
  - Batch processing: configurable embed_batch_size for large documents
  - Metadata: exam_id, doc_type tagged on every node
  - Filter by metadata at query time
"""

import logging
import time
from typing import Optional
from uuid import UUID

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import get_settings
from app.core.exceptions import EmbeddingException

logger = logging.getLogger(__name__)

# ── Singleton clients (lazy init) ─────────────────────────────────────────────

_qdrant_client: Optional[QdrantClient] = None
_qdrant_async_client: Optional[AsyncQdrantClient] = None
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
            check_compatibility=False,
        )
        logger.info(
            "Connected to Qdrant at %s:%s", settings.qdrant_host, settings.qdrant_port
        )
    return _qdrant_client


async def get_qdrant_async_client() -> AsyncQdrantClient:
    """Get or create a singleton Async Qdrant client."""
    global _qdrant_async_client
    if _qdrant_async_client is None:
        settings = get_settings()
        _qdrant_async_client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            check_compatibility=False,
        )
        logger.info(
            "Connected to Async Qdrant at %s:%s",
            settings.qdrant_host,
            settings.qdrant_port,
        )
    return _qdrant_async_client


def get_embed_model() -> HuggingFaceEmbedding:
    """Get or create a singleton BGE-M3 embedding model."""
    global _embed_model
    if _embed_model is None:
        settings = get_settings()
        logger.info(
            "Loading embedding model '%s' on device '%s'...",
            settings.embedding_model,
            settings.embedding_device,
        )
        _embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
            embed_batch_size=settings.embedding_batch_size,
        )
        logger.info(
            "Embedding model loaded (batch_size=%d)", settings.embedding_batch_size
        )
    return _embed_model


def _get_vector_store() -> QdrantVectorStore:
    """Get Qdrant vector store for the exam documents collection (sync)."""
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=COLLECTION_NAME,
    )


async def _get_async_vector_store() -> QdrantVectorStore:
    """Get Qdrant vector store for the exam documents collection (async)."""
    aclient = await get_qdrant_async_client()
    return QdrantVectorStore(
        aclient=aclient,
        collection_name=COLLECTION_NAME,
    )


async def embed_document(
    exam_id: UUID,
    doc_id: UUID,
    doc_type: str,
    text: str,
) -> int:
    """Embed document text and store chunks in Qdrant.

    Sprint 4: ใช้ configurable chunk_size, chunk_overlap, และ embed_batch_size
    จาก Settings เพื่อให้ปรับ performance ได้ผ่าน environment variables.

    Args:
        exam_id:  UUID ของข้อสอบที่เอกสารนี้เป็นของ
        doc_id:   UUID ของ document record (สำหรับ tracking)
        doc_type: 'answer_key' | 'rubric' | 'course_material'
        text:     ข้อความเต็มที่ extract จาก PDF

    Returns:
        จำนวน chunks ที่ embed แล้ว
    """
    settings = get_settings()
    start_time = time.time()

    try:
        # Configure LlamaIndex settings — ใช้ค่าจาก config แทน hardcode
        embed_model = get_embed_model()
        Settings.embed_model = embed_model
        Settings.node_parser = SentenceSplitter(
            chunk_size=settings.embedding_chunk_size,
            chunk_overlap=settings.embedding_chunk_overlap,
        )

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
        elapsed = time.time() - start_time
        logger.info(
            "Embedded document doc_id=%s (exam_id=%s, type=%s): %d chunks in %.2fs "
            "(chunk_size=%d, overlap=%d, batch_size=%d)",
            doc_id,
            exam_id,
            doc_type,
            chunk_count,
            elapsed,
            settings.embedding_chunk_size,
            settings.embedding_chunk_overlap,
            settings.embedding_batch_size,
        )
        return chunk_count

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "Embedding failed for doc_id=%s after %.2fs: %s", doc_id, elapsed, e
        )
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
