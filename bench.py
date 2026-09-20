"""
Benchmark Script for Lab 07 (K4-L3B: Shopee E-Commerce Policies).
Compares retrieval strategies across the Shopee policy documents.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    compute_similarity,
)
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

# Xác định thư mục dữ liệu .md
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "shopee-returns"
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR / "data" / "shopee"
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR / "data"


class HeadingChunker:
    """Chunk Markdown text by headings (#, ##, ###), keeping header context in subchunks."""

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.recursive_fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        sections = re.split(r"(?m)(?=^#{1,3}\s+)", text.strip())
        chunks: list[str] = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                header = lines[0] if lines else ""
                body = lines[1] if len(lines) > 1 else ""
                sub_chunks = self.recursive_fallback.chunk(body)
                for sub in sub_chunks:
                    chunks.append(f"{header}\n{sub}".strip())
        return chunks


# 1. Đọc từng file .md, tách frontmatter thành metadata và phần thân thành content
def load_corpus(data_dir: Path) -> list[tuple[Path, dict[str, str], str]]:
    """Đọc từng file .md, tách frontmatter thành metadata và phần thân thành content."""
    documents: list[tuple[Path, dict[str, str], str]] = []
    for file_path in sorted(data_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        frontmatter: dict[str, str] = {}
        content = text

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                raw_fm = parts[1]
                content = parts[2].strip()
                for line in raw_fm.splitlines():
                    match = re.match(r"^(\w+):\s*[\"']?(.*?)[\"']?\s*$", line.strip())
                    if match:
                        frontmatter[match.group(1)] = match.group(2)

        documents.append((file_path, frontmatter, content))
    return documents


# Danh sách 5 query đánh giá kèm gold answer
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho đơn hàng thực phẩm tươi sống là bao lâu?",
        "gold_answer": "Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái Giao hàng thành công.",
        "gold_doc": "shopee-return-refund-policy-buyer",
        "filter": None,
        "target_phrase": "24 giờ",
    },
    {
        "id": 2,
        "query": "Người bán có bao nhiêu ngày để gửi phản hồi nếu không đồng ý với quyết định hoàn tiền của Shopee cho Người mua?",
        "gold_answer": "Người bán cần gửi phản hồi trong vòng 02 ngày lịch kể từ ngày nhận được thông báo của Shopee.",
        "gold_doc": "shopee-return-refund-policy-seller",
        "filter": {"audience": "seller"},
        "target_phrase": "trong vòng 02 ngày lịch",
    },
    {
        "id": 3,
        "query": "Sau khi Shopee chấp nhận hoàn tiền, thời gian nhận được tiền hoàn qua Thẻ tín dụng/ghi nợ là bao lâu?",
        "gold_answer": "Từ 7 - 14 ngày làm việc (tùy theo ngân hàng phát hành thẻ).",
        "gold_doc": "refund-timeline-and-check",
        "filter": {"category": "Hoàn tiền"},
        "target_phrase": "7 - 14 ngày làm việc",
    },
    {
        "id": 4,
        "query": "Những đối tượng Người mua nào được áp dụng chính sách Trả hàng do Đổi ý/không còn nhu cầu?",
        "gold_answer": "Người mua là thành viên Chương trình Khách hàng thân thiết Shopee đạt hạng Vàng/Kim Cương và/hoặc đang sử dụng Gói ShopeeVIP.",
        "gold_doc": "about-change-of-mind-returns-buyer",
        "filter": None,
        "target_phrase": "hạng Vàng/Kim Cương và/hoặc đang sử dụng Gói ShopeeVIP",
    },
    {
        "id": 5,
        "query": "Thời hạn khiếu nại quyết định Trả hàng/Hoàn tiền đối với Người mua là bao nhiêu ngày?",
        "gold_answer": "Người mua có 15 ngày kể từ ngày giao hàng; Người bán có 2 ngày kể từ khi nhận được thông báo để khiếu nại.",
        "gold_doc": "shopee-return-refund-policy-buyer",
        "filter": {"audience": "buyer"},
        "target_phrase": "15 ngày",
    },
]


def run_benchmark(strategy_name: str, chunker, data_dir: Path = DATA_DIR) -> str:
    output_lines: list[str] = []
    output_lines.append("=" * 60)
    output_lines.append(f"BENCHMARK RUN: Strategy = {strategy_name}")
    output_lines.append("=" * 60)

    # 1. Đọc từng file .md, tách frontmatter thành metadata và phần thân thành content
    corpus = load_corpus(data_dir)

    # 2. Chunk phần thân, mỗi chunk thành một Document:
    #       Document(id=f"{path.stem}#{i}", content=chunk,
    #                metadata={**frontmatter, "doc_id": path.stem, ...})
    docs_to_add: list[Document] = []
    for path, frontmatter, content in corpus:
        chunks = chunker.chunk(content)
        for i, chunk in enumerate(chunks):
            doc = Document(
                id=f"{path.stem}#{i}",
                content=chunk,
                metadata={
                    **frontmatter,
                    "doc_id": path.stem,
                    "chunk_index": i,
                },
            )
            docs_to_add.append(doc)

    output_lines.append(f"Loaded {len(corpus)} files from {data_dir} -> Total chunks indexed: {len(docs_to_add)}")

    # 3. Nạp vào EmbeddingStore, chạy 5 query qua search_with_filter()
    store = EmbeddingStore(collection_name=f"shopee_{strategy_name}", embedding_fn=_mock_embed)
    store.add_documents(docs_to_add)

    correct_count = 0
    # 4. In top-3 kèm score và doc_id để đối chiếu với gold answer
    for q in BENCHMARK_QUERIES:
        query_text = q["query"]
        metadata_filter = q.get("filter")
        results = store.search_with_filter(query_text, top_k=3, metadata_filter=metadata_filter)

        output_lines.append(f"\n--- Query {q['id']}: {query_text} ---")
        if metadata_filter:
            output_lines.append(f"  [Filter]: {metadata_filter}")
        output_lines.append(f"  [Gold Answer]: {q['gold_answer']}")
        output_lines.append(f"  [Top-3 Retrieval Results]:")

        is_relevant = False
        for rank, res in enumerate(results, 1):
            doc = res["metadata"].get("doc_id", "N/A")
            score = res["score"]
            text_preview = res["content"][:100].replace("\n", " ")
            has_phrase = q["target_phrase"].lower() in res["content"].lower()
            if has_phrase or doc == q["gold_doc"]:
                is_relevant = True
            output_lines.append(f"    Top-{rank} (Score: {score:.4f}, doc_id: {doc}): {text_preview}...")

        if is_relevant:
            correct_count += 1
            output_lines.append("  -> Evaluation: PASS (Found relevant context in Top-3)")
        else:
            output_lines.append("  -> Evaluation: MISS")

    summary = f"\nSummary for {strategy_name}: {correct_count}/{len(BENCHMARK_QUERIES)} relevant in Top-3\n"
    output_lines.append(summary)

    result_text = "\n".join(output_lines)
    return result_text


if __name__ == "__main__":
    strategies = {
        "SentenceChunker": SentenceChunker(max_sentences_per_chunk=2),
        "FixedSizeChunker": FixedSizeChunker(chunk_size=300, overlap=30),
        "RecursiveChunker": RecursiveChunker(chunk_size=350),
        "HeadingChunker": HeadingChunker(max_chunk_size=400),
    }

    full_report = []
    for name, chunker in strategies.items():
        res = run_benchmark(name, chunker)
        print(res)
        full_report.append(res)

    Path("ket_qua_benchmark.txt").write_text("\n".join(full_report), encoding="utf-8")
    print("Saved all benchmark comparisons successfully to ket_qua_benchmark.txt")