"""
Unit tests for rag_service — Sprint 2 BE-S.

Tests:
  - query_for_grading: returns score + reasoning from mock LLM
  - query_for_grading: clamps score to [0, max_score]
  - query_for_grading: raises LLMException when LLM returns invalid JSON
  - query_for_grading: raises LLMException on Groq API error
  - _parse_json_from_response: parses clean JSON
  - _parse_json_from_response: extracts JSON from noisy text
  - _parse_json_from_response: raises ValueError on missing JSON
  - retrieve_context: returns context text from mock retriever
  - retrieve_context: returns fallback text when no chunks found
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from llama_index.core.llms import ChatMessage

from app.core.exceptions import LLMException
from app.services.rag_service import _parse_json_from_response


# ── Tests: _parse_json_from_response ─────────────────────────────────────────

class TestParseJsonFromResponse:
    def test_clean_json(self):
        payload = {"score": 8.5, "reasoning": "Good answer", "covered_points": [], "missed_points": []}
        result = _parse_json_from_response(json.dumps(payload))
        assert result["score"] == 8.5
        assert result["reasoning"] == "Good answer"

    def test_json_embedded_in_text(self):
        raw = 'Here is my evaluation:\n{"score": 7.0, "reasoning": "Partial"}\nDone.'
        result = _parse_json_from_response(raw)
        assert result["score"] == 7.0

    def test_raises_on_no_json(self):
        with pytest.raises(ValueError, match="No valid JSON"):
            _parse_json_from_response("ตอบกลับไม่ถูกต้อง ไม่มี JSON")

    def test_json_with_whitespace(self):
        raw = '   {"score": 10, "reasoning": "Perfect"}   '
        result = _parse_json_from_response(raw)
        assert result["score"] == 10

    def test_json_with_thai_content(self):
        raw = '{"score": 6.5, "reasoning": "ตอบได้บางส่วน"}'
        result = _parse_json_from_response(raw)
        assert result["reasoning"] == "ตอบได้บางส่วน"


# ── Tests: query_for_grading ──────────────────────────────────────────────────

@pytest.mark.asyncio
class TestQueryForGrading:

    @patch("app.services.rag_service._get_groq_llm")
    @patch("app.services.rag_service.retrieve_context")
    async def test_returns_score_and_reasoning(self, mock_retrieve, mock_get_llm):
        """query_for_grading should return correct score and reasoning dict."""
        from app.services.rag_service import query_for_grading

        mock_retrieve.return_value = "เฉลย: พืชใช้แสงอาทิตย์ CO2 และน้ำ"

        llm_response = MagicMock()
        llm_response.message.content = json.dumps({
            "score": 8.0,
            "reasoning": "ตอบถูกต้องส่วนใหญ่",
            "covered_points": ["แสง", "CO2"],
            "missed_points": ["น้ำ"],
        })
        mock_llm = MagicMock()
        mock_llm.chat.return_value = llm_response
        mock_get_llm.return_value = mock_llm

        result = await query_for_grading(
            exam_id=uuid4(),
            question_text="อธิบายการสังเคราะห์แสง",
            student_answer="พืชใช้แสงอาทิตย์และ CO2 ในการสังเคราะห์อาหาร",
            max_score=10.0,
        )

        assert result["score"] == 8.0
        assert result["reasoning"] == "ตอบถูกต้องส่วนใหญ่"
        assert "CO2" in result["covered_points"]
        assert "น้ำ" in result["missed_points"]

    @patch("app.services.rag_service._get_groq_llm")
    @patch("app.services.rag_service.retrieve_context")
    async def test_clamps_score_above_max(self, mock_retrieve, mock_get_llm):
        """query_for_grading should clamp score to max_score if LLM overshoots."""
        from app.services.rag_service import query_for_grading

        mock_retrieve.return_value = "context"
        llm_response = MagicMock()
        llm_response.message.content = json.dumps({"score": 15.0, "reasoning": "Over full"})
        mock_llm = MagicMock()
        mock_llm.chat.return_value = llm_response
        mock_get_llm.return_value = mock_llm

        result = await query_for_grading(uuid4(), "question", "answer", max_score=10.0)
        assert result["score"] == 10.0

    @patch("app.services.rag_service._get_groq_llm")
    @patch("app.services.rag_service.retrieve_context")
    async def test_clamps_score_below_zero(self, mock_retrieve, mock_get_llm):
        """query_for_grading should clamp score to 0 if LLM returns negative."""
        from app.services.rag_service import query_for_grading

        mock_retrieve.return_value = "context"
        llm_response = MagicMock()
        llm_response.message.content = json.dumps({"score": -2.0, "reasoning": "Wrong"})
        mock_llm = MagicMock()
        mock_llm.chat.return_value = llm_response
        mock_get_llm.return_value = mock_llm

        result = await query_for_grading(uuid4(), "question", "answer", max_score=10.0)
        assert result["score"] == 0.0

    @patch("app.services.rag_service._get_groq_llm")
    @patch("app.services.rag_service.retrieve_context")
    async def test_raises_on_invalid_json(self, mock_retrieve, mock_get_llm):
        """query_for_grading should raise LLMException when LLM returns no JSON."""
        from app.services.rag_service import query_for_grading

        mock_retrieve.return_value = "context"
        llm_response = MagicMock()
        llm_response.message.content = "ขออภัย ไม่สามารถประเมินได้ในขณะนี้"
        mock_llm = MagicMock()
        mock_llm.chat.return_value = llm_response
        mock_get_llm.return_value = mock_llm

        with pytest.raises(LLMException):
            await query_for_grading(uuid4(), "question", "answer", max_score=10.0)

    @patch("app.services.rag_service._get_groq_llm")
    @patch("app.services.rag_service.retrieve_context")
    async def test_raises_on_groq_api_error(self, mock_retrieve, mock_get_llm):
        """query_for_grading should raise LLMException on Groq API failure."""
        from app.services.rag_service import query_for_grading

        mock_retrieve.return_value = "context"
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = RuntimeError("Groq 429 Too Many Requests")
        mock_get_llm.return_value = mock_llm

        with pytest.raises(LLMException, match="Groq 429"):
            await query_for_grading(uuid4(), "question", "answer", max_score=10.0)


# ── Tests: retrieve_context ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestRetrieveContext:

    @patch("app.services.rag_service.get_index_for_exam")
    @patch("app.services.rag_service.get_embed_model")
    @patch("app.services.rag_service.Settings")
    async def test_returns_context_text(self, mock_settings, mock_embed, mock_get_index):
        """retrieve_context should return concatenated chunk text."""
        from app.services.rag_service import retrieve_context

        mock_embed.return_value = MagicMock()

        node1 = MagicMock()
        node1.text = "เฉลย: พืชสังเคราะห์แสงโดยใช้ CO2"
        node1.metadata = {"doc_type": "answer_key"}
        node2 = MagicMock()
        node2.text = "Rubric: ต้องระบุวัตถุดิบ"
        node2.metadata = {"doc_type": "rubric"}

        mock_retriever = MagicMock()
        mock_retriever.aretrieve = AsyncMock(return_value=[node1, node2])

        mock_index = MagicMock()
        mock_index.as_retriever.return_value = mock_retriever
        mock_get_index.return_value = mock_index

        result = await retrieve_context(uuid4(), "อธิบายการสังเคราะห์แสง")

        assert "เฉลย" in result
        assert "Rubric" in result

    @patch("app.services.rag_service.get_index_for_exam")
    @patch("app.services.rag_service.get_embed_model")
    @patch("app.services.rag_service.Settings")
    async def test_returns_fallback_when_no_chunks(self, mock_settings, mock_embed, mock_get_index):
        """retrieve_context should return fallback text when no chunks found."""
        from app.services.rag_service import retrieve_context

        mock_embed.return_value = MagicMock()

        mock_retriever = MagicMock()
        mock_retriever.aretrieve = AsyncMock(return_value=[])

        mock_index = MagicMock()
        mock_index.as_retriever.return_value = mock_retriever
        mock_get_index.return_value = mock_index

        result = await retrieve_context(uuid4(), "คำถาม")
        assert "ไม่พบเนื้อหาอ้างอิง" in result

    @patch("app.services.rag_service.get_index_for_exam")
    @patch("app.services.rag_service.get_embed_model")
    @patch("app.services.rag_service.Settings")
    async def test_uses_exam_id_metadata_filter(self, mock_settings, mock_embed, mock_get_index):
        """retrieve_context must pass MetadataFilters with exam_id — not a raw dict."""
        from app.services.rag_service import retrieve_context
        from llama_index.core.vector_stores import MetadataFilters

        mock_embed.return_value = MagicMock()
        exam_id = uuid4()

        mock_retriever = MagicMock()
        mock_retriever.aretrieve = AsyncMock(return_value=[])
        mock_index = MagicMock()
        mock_index.as_retriever.return_value = mock_retriever
        mock_get_index.return_value = mock_index

        await retrieve_context(exam_id, "คำถาม")

        _, kwargs = mock_index.as_retriever.call_args
        assert "filters" in kwargs
        assert isinstance(kwargs["filters"], MetadataFilters)
        assert kwargs["filters"].filters[0].key == "exam_id"
        assert kwargs["filters"].filters[0].value == str(exam_id)


# ── Tests: _call_llm_with_retry ─────────────────────────────────────────

@pytest.mark.asyncio
class TestCallLlmWithRetry:

    async def test_returns_on_success(self):
        """Should return content on first successful call."""
        from app.services.rag_service import _call_llm_with_retry

        llm = MagicMock()
        response = MagicMock()
        response.message.content = '{"score": 8.0}'
        llm.chat.return_value = response

        result = await _call_llm_with_retry(llm, [ChatMessage(role="user", content="test")])
        assert result == '{"score": 8.0}'
        assert llm.chat.call_count == 1

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_retries_on_429_then_succeeds(self, mock_sleep):
        """Should retry after 429 and return on subsequent success."""
        from app.services.rag_service import _call_llm_with_retry

        llm = MagicMock()
        response = MagicMock()
        response.message.content = '{"score": 5.0}'
        llm.chat.side_effect = [RuntimeError("429 Too Many Requests"), response]

        result = await _call_llm_with_retry(llm, [ChatMessage(role="user", content="test")])

        assert result == '{"score": 5.0}'
        assert llm.chat.call_count == 2
        mock_sleep.assert_awaited_once()

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_raises_after_max_retries(self, mock_sleep):
        """Should raise after exhausting all retries on 429."""
        from app.services.rag_service import _call_llm_with_retry

        llm = MagicMock()
        llm.chat.side_effect = RuntimeError("429 Too Many Requests")

        with pytest.raises(RuntimeError, match="429"):
            await _call_llm_with_retry(llm, [ChatMessage(role="user", content="test")])

        assert llm.chat.call_count == 3  # all retries exhausted

    async def test_does_not_retry_non_rate_limit_error(self):
        """Non-429 errors should raise immediately without any retry."""
        from app.services.rag_service import _call_llm_with_retry

        llm = MagicMock()
        llm.chat.side_effect = RuntimeError("Connection refused")

        with pytest.raises(RuntimeError, match="Connection refused"):
            await _call_llm_with_retry(llm, [ChatMessage(role="user", content="test")])

        assert llm.chat.call_count == 1  # no retries
