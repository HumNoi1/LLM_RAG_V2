"""
Tests for app.services.embedding_service

All heavy I/O (HuggingFace model load, Qdrant client) is mocked so these tests
run without GPU or a running Qdrant instance.

Covers:
  - embed_document() happy path → returns chunk count
  - embed_document() propagates EmbeddingException on Qdrant error
  - delete_exam_embeddings() happy path (collection exists)
  - delete_exam_embeddings() no-op when collection does not exist
  - delete_exam_embeddings() propagates EmbeddingException on error
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import UUID

from app.core.exceptions import EmbeddingException
from app.services import embedding_service


EXAM_ID = UUID("11111111-1111-1111-1111-111111111111")
DOC_ID = UUID("22222222-2222-2222-2222-222222222222")
SAMPLE_TEXT = "This is the answer key for the midterm exam."


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_mock_embed_model():
    model = MagicMock()
    return model


def _make_mock_qdrant_client(collection_exists: bool = True, scroll_points: int = 3):
    client = MagicMock()
    client.collection_exists.return_value = collection_exists

    # scroll returns (list_of_points, next_offset)
    fake_points = [MagicMock() for _ in range(scroll_points)]
    client.scroll.return_value = (fake_points, None)

    return client


# ── embed_document ────────────────────────────────────────────────────────────


class TestEmbedDocument:
    def test_returns_chunk_count(self):
        mock_embed = _make_mock_embed_model()
        mock_client = _make_mock_qdrant_client(scroll_points=4)

        with (
            patch.object(
                embedding_service, "_get_embed_model", return_value=mock_embed
            ),
            patch.object(
                embedding_service, "_get_qdrant_client", return_value=mock_client
            ),
            patch("app.services.embedding_service.QdrantVectorStore") as mock_vs_cls,
            patch("app.services.embedding_service.StorageContext") as mock_sc_cls,
            patch("app.services.embedding_service.VectorStoreIndex") as mock_idx_cls,
            patch("app.services.embedding_service.Settings"),
        ):
            mock_vs_cls.return_value = MagicMock()
            mock_sc_cls.from_defaults.return_value = MagicMock()
            mock_idx_cls.from_documents.return_value = MagicMock()

            result = embedding_service.embed_document(
                exam_id=EXAM_ID,
                doc_id=DOC_ID,
                doc_type="answer_key",
                text=SAMPLE_TEXT,
            )

        assert result == 4

    def test_raises_embedding_exception_on_qdrant_error(self):
        mock_embed = _make_mock_embed_model()
        mock_client = MagicMock()
        mock_client.scroll.side_effect = RuntimeError("Qdrant connection refused")

        with (
            patch.object(
                embedding_service, "_get_embed_model", return_value=mock_embed
            ),
            patch.object(
                embedding_service, "_get_qdrant_client", return_value=mock_client
            ),
            patch("app.services.embedding_service.QdrantVectorStore"),
            patch("app.services.embedding_service.StorageContext") as mock_sc_cls,
            patch("app.services.embedding_service.VectorStoreIndex") as mock_idx_cls,
            patch("app.services.embedding_service.Settings"),
        ):
            mock_sc_cls.from_defaults.return_value = MagicMock()
            mock_idx_cls.from_documents.return_value = MagicMock()

            with pytest.raises(EmbeddingException):
                embedding_service.embed_document(
                    exam_id=EXAM_ID,
                    doc_id=DOC_ID,
                    doc_type="rubric",
                    text=SAMPLE_TEXT,
                )


# ── delete_exam_embeddings ────────────────────────────────────────────────────


class TestDeleteExamEmbeddings:
    def test_deletes_when_collection_exists(self):
        mock_client = _make_mock_qdrant_client(collection_exists=True)

        with patch.object(
            embedding_service, "_get_qdrant_client", return_value=mock_client
        ):
            embedding_service.delete_exam_embeddings(EXAM_ID)

        mock_client.delete.assert_called_once()

    def test_no_op_when_collection_missing(self):
        mock_client = _make_mock_qdrant_client(collection_exists=False)

        with patch.object(
            embedding_service, "_get_qdrant_client", return_value=mock_client
        ):
            embedding_service.delete_exam_embeddings(EXAM_ID)

        mock_client.delete.assert_not_called()

    def test_raises_embedding_exception_on_error(self):
        mock_client = MagicMock()
        mock_client.collection_exists.side_effect = RuntimeError("Qdrant down")

        with patch.object(
            embedding_service, "_get_qdrant_client", return_value=mock_client
        ):
            with pytest.raises(EmbeddingException):
                embedding_service.delete_exam_embeddings(EXAM_ID)
