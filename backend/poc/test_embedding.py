"""
PoC: BGE-M3 Embedding + Qdrant — Thai language test

Validates:
  - BGE-M3 (BAAI/bge-m3) can embed Thai text
  - Qdrant stores and retrieves vectors correctly
  - Semantic search returns relevant Thai results

Prerequisites:
  1. docker compose up -d       (start Qdrant)
  2. pip install -r requirements.txt
  3. python poc/test_embedding.py

Expected output: ✅ PoC passed!
"""
import os
import sys

# Add backend root to path so we can import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# ── Test data ─────────────────────────────────────────────────────────────────

THAI_DOCUMENTS = [
    "การสังเคราะห์แสงคือกระบวนการที่พืชสีเขียวใช้พลังงานจากแสงอาทิตย์ "
    "เพื่อเปลี่ยนคาร์บอนไดออกไซด์และน้ำให้เป็นกลูโคสและออกซิเจน "
    "ซึ่งเป็นกระบวนการพื้นฐานที่สนับสนุนห่วงโซ่อาหารทั้งหมดบนโลก",

    "ปฏิกิริยาเคมีคือกระบวนการที่สารตั้งต้นเปลี่ยนแปลงไปเป็นสารผลิตภัณฑ์ใหม่ "
    "โดยมีการเปลี่ยนแปลงพลังงานและการจัดเรียงอะตอมใหม่ "
    "ปฏิกิริยาแบ่งออกเป็นประเภทคายความร้อนและดูดความร้อน",

    "DNA หรือกรดดีออกซีไรโบนิวคลีอิก คือโมเลกุลที่บรรจุข้อมูลทางพันธุกรรม "
    "ในรูปของลำดับนิวคลีโอไทด์ 4 ชนิด ได้แก่ อะดีนีน ไทมีน กัวนีน และไซโทซีน "
    "DNA ถูกถ่ายทอดจากพ่อแม่ไปสู่ลูกหลาน",
]

# Semantic query — should match document 1 (photosynthesis)
TEST_QUERY = "พืชสร้างอาหารและออกซิเจนได้อย่างไร"
EXPECTED_TOP_KEYWORD = "การสังเคราะห์แสง"


def main() -> None:
    print("=" * 60)
    print("PoC: BGE-M3 Embedding + Qdrant (Thai)")
    print("=" * 60)

    # 1. Connect to Qdrant
    print("\n[1] Connecting to Qdrant (localhost:6333)...")
    client = QdrantClient(host="localhost", port=6333)
    collections = client.get_collections()
    print(f"    Connected — existing collections: {[c.name for c in collections.collections]}")

    # 2. Load BGE-M3
    print("\n[2] Loading BAAI/bge-m3 embedding model...")
    print("    (First run downloads ~2.3 GB — subsequent runs use cache)")
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-m3",
        device="cpu",
    )
    Settings.embed_model = embed_model
    # Use same chunking strategy as production
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    print("    Model loaded!")

    # 3. Prepare collection
    collection_name = "poc_thai_test"
    print(f"\n[3] Setting up Qdrant collection '{collection_name}'...")
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        print("    Cleaned up old collection")

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 4. Embed and index documents
    print(f"\n[4] Embedding {len(THAI_DOCUMENTS)} Thai documents...")
    docs = [
        Document(text=text, metadata={"doc_type": "course_material", "exam_id": "poc-test"})
        for text in THAI_DOCUMENTS
    ]
    index = VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        show_progress=True,
    )
    print("    Documents embedded and stored in Qdrant!")

    # 5. Semantic search
    print(f"\n[5] Query: '{TEST_QUERY}'")
    retriever = index.as_retriever(similarity_top_k=2)
    results = retriever.retrieve(TEST_QUERY)

    print("\n    Results:")
    for i, node in enumerate(results, 1):
        preview = node.text[:80].replace("\n", " ")
        print(f"    [{i}] score={node.score:.4f} | {preview}...")

    # 6. Assert correctness
    assert len(results) > 0, "No results returned!"
    top_text = results[0].text
    assert EXPECTED_TOP_KEYWORD in top_text, (
        f"Expected top result to mention '{EXPECTED_TOP_KEYWORD}', got: {top_text[:100]}"
    )
    print(f"\n    ✓ Top result correctly mentions '{EXPECTED_TOP_KEYWORD}'")

    # 7. Cleanup
    client.delete_collection(collection_name)
    print("\n    Cleaned up test collection")

    print("\n" + "=" * 60)
    print("✅  PoC PASSED — BGE-M3 + Qdrant working correctly with Thai")
    print("=" * 60)


if __name__ == "__main__":
    main()
