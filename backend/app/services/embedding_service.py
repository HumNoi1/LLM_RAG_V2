"""
Embedding Service — BGE-M3 embeddings + Qdrant vector store.
BE-S responsibility (Sprint 2).

Key design decisions:
  - Model: BAAI/bge-m3 (multilingual, strong Thai support)
  - Chunking: SentenceSplitter(chunk_size=512, chunk_overlap=50)
  - Metadata: exam_id, doc_type tagged on every node
  - Collection per deployment (not per exam) — filter by metadata at query time
"""
from typing import List
from uuid import UUID


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

    Sprint 2 implementation.
    """
    raise NotImplementedError("embedding_service.embed_document — implement in Sprint 2")


async def delete_exam_embeddings(exam_id: UUID) -> None:
    """Delete all Qdrant points associated with an exam.

    Sprint 2 implementation.
    """
    raise NotImplementedError("embedding_service.delete_exam_embeddings — implement in Sprint 2")
