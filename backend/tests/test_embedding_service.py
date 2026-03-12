"""
Unit tests for embedding_service — Sprint 2 BE-S.

Tests:
  - embed_document: embeds text and returns chunk count
  - embed_document: failure raises EmbeddingException
  - delete_exam_embeddings: deletes points for exam
  - get_index_for_exam: returns a VectorStoreIndex
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.exceptions import EmbeddingException


# ── Tests: embed_document ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestEmbedDocument:

    @patch("app.services.embedding_service.VectorStoreIndex")
    @patch("app.services.embedding_service.StorageContext")
    @patch("app.services.embedding_service.Settings")
    @patch("app.services.embedding_service._get_vector_store")
    @patch("app.services.embedding_service.get_embed_model")
    async def test_embed_returns_chunk_count(self, mock_get_embed, mock_vs, mock_settings, mock_sc, mock_index_cls):
        """embed_document should return the number of chunks stored."""
        from app.services.embedding_service import embed_document

        mock_get_embed.return_value = MagicMock()
        mock_vs.return_value = MagicMock()

        mock_sc_instance = MagicMock()
        mock_sc.from_defaults.return_value = mock_sc_instance

        mock_index = MagicMock()
        mock_index.docstore.docs = {"c1": MagicMock(), "c2": MagicMock(), "c3": MagicMock()}
        mock_index_cls.from_documents.return_value = mock_index

        result = await embed_document(uuid4(), uuid4(), "answer_key", "สังเคราะห์แสง" * 20)

        assert result == 3
        mock_index_cls.from_documents.assert_called_once()

    @patch("app.services.embedding_service.VectorStoreIndex")
    @patch("app.services.embedding_service.StorageContext")
    @patch("app.services.embedding_service.Settings")
    @patch("app.services.embedding_service._get_vector_store")
    @patch("app.services.embedding_service.get_embed_model")
    async def test_embed_raises_on_failure(self, mock_get_embed, mock_vs, mock_settings, mock_sc, mock_index_cls):
        """embed_document should raise EmbeddingException on failure."""
        from app.services.embedding_service import embed_document

        mock_get_embed.return_value = MagicMock()
        mock_vs.return_value = MagicMock()
        mock_index_cls.from_documents.side_effect = RuntimeError("Qdrant connection refused")

        with pytest.raises(EmbeddingException, match="Qdrant connection refused"):
            await embed_document(uuid4(), uuid4(), "rubric", "test text")


# ── Tests: delete_exam_embeddings ─────────────────────────────────────────────

@pytest.mark.asyncio
class TestDeleteExamEmbeddings:

    @patch("app.services.embedding_service.get_qdrant_client")
    async def test_delete_calls_qdrant(self, mock_get_client):
        """delete_exam_embeddings should call qdrant client.delete."""
        from app.services.embedding_service import delete_exam_embeddings

        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_get_client.return_value = mock_client

        await delete_exam_embeddings(uuid4())

        mock_client.delete.assert_called_once()

    @patch("app.services.embedding_service.get_qdrant_client")
    async def test_delete_noop_if_no_collection(self, mock_get_client):
        """delete_exam_embeddings should do nothing if collection doesn't exist."""
        from app.services.embedding_service import delete_exam_embeddings

        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False
        mock_get_client.return_value = mock_client

        await delete_exam_embeddings(uuid4())
        mock_client.delete.assert_not_called()

    @patch("app.services.embedding_service.get_qdrant_client")
    async def test_delete_raises_on_failure(self, mock_get_client):
        """delete_exam_embeddings should raise EmbeddingException on error."""
        from app.services.embedding_service import delete_exam_embeddings

        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        mock_client.delete.side_effect = RuntimeError("Connection lost")
        mock_get_client.return_value = mock_client

        with pytest.raises(EmbeddingException, match="Connection lost"):
            await delete_exam_embeddings(uuid4())


# ── Tests: get_index_for_exam ─────────────────────────────────────────────────

class TestGetIndexForExam:

    @patch("app.services.embedding_service.VectorStoreIndex")
    @patch("app.services.embedding_service.Settings")
    @patch("app.services.embedding_service._get_vector_store")
    @patch("app.services.embedding_service.get_embed_model")
    def test_returns_index(self, mock_get_embed, mock_vs, mock_settings, mock_index_cls):
        """get_index_for_exam should return a VectorStoreIndex."""
        from app.services.embedding_service import get_index_for_exam

        mock_get_embed.return_value = MagicMock()
        mock_vs.return_value = MagicMock()
        mock_index = MagicMock()
        mock_index_cls.from_vector_store.return_value = mock_index

        result = get_index_for_exam(uuid4())
        assert result == mock_index
