"""
Embedding Service — BGE-M3 embeddings + Qdrant vector store.
BE-S responsibility (Sprint 2).

Key design decisions:
  - Model: BAAI/bge-m3 (multilingual, strong Thai support)
  - Chunking: SentenceSplitter(chunk_size=512, chunk_overlap=50)
  - Metadata: exam_id, doc_type tagged on every node
  - Collection per deployment (not per exam) — filter by metadata at query time
"""
import logging
from functools import lru_cache
from uuid import UUID

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import get_settings
from app.core.exceptions import EmbeddingException

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_embed_model() -> HuggingFaceEmbedding:
    """Load BGE-M3 model once and cache it for the process lifetime."""
    settings = get_settings()
    logger.info("Loading embedding model %s on device=%s …", settings.embedding_model, settings.embedding_device)
    model = HuggingFaceEmbedding(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )
    logger.info("Embedding model loaded.")
    return model


@lru_cache(maxsize=1)
def _get_qdrant_client() -> QdrantClient:
    """Create a Qdrant client singleton."""
    settings = get_settings()
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def _collection_name() -> str:
    return get_settings().qdrant_collection_name


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

    Raises:
        EmbeddingException: on any embedding / Qdrant error.
    """
    try:
        embed_model = _get_embed_model()
        client = _get_qdrant_client()
        collection = _collection_name()

        # Configure LlamaIndex global settings for this call
        Settings.embed_model = embed_model
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

        vector_store = QdrantVectorStore(client=client, collection_name=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        doc = Document(
            text=text,
            metadata={
                "exam_id": str(exam_id),
                "doc_id": str(doc_id),
                "doc_type": doc_type,
            },
        )

        index = VectorStoreIndex.from_documents(
            [doc],
            storage_context=storage_context,
            show_progress=False,
        )

        # Count how many nodes (chunks) were inserted
        # LlamaIndex doesn't expose chunk count directly; count via Qdrant scroll
        result = client.scroll(
            collection_name=collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=str(doc_id)),
                    )
                ]
            ),
            limit=10_000,
            with_payload=False,
            with_vectors=False,
        )
        chunk_count = len(result[0])  # result is (points, next_page_offset)
        logger.info("Embedded doc_id=%s into %d chunks (exam=%s)", doc_id, chunk_count, exam_id)
        return chunk_count

    except Exception as exc:
        logger.exception("embed_document failed for doc_id=%s: %s", doc_id, exc)
        raise EmbeddingException(str(exc)) from exc


async def delete_exam_embeddings(exam_id: UUID) -> None:
    """Delete all Qdrant points associated with an exam.

    Raises:
        EmbeddingException: on any Qdrant error.
    """
    try:
        client = _get_qdrant_client()
        collection = _collection_name()

        if not client.collection_exists(collection):
            return  # Nothing to delete

        client.delete(
            collection_name=collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="exam_id",
                        match=MatchValue(value=str(exam_id)),
                    )
                ]
            ),
        )
        logger.info("Deleted all Qdrant points for exam_id=%s", exam_id)
    except Exception as exc:
        logger.exception("delete_exam_embeddings failed for exam_id=%s: %s", exam_id, exc)
        raise EmbeddingException(str(exc)) from exc
