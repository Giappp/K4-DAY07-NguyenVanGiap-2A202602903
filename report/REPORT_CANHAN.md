# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Giáp
**Nhóm:** TenNhuCu
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine đo mức độ tương đồng giữa 2 vector, độ tương tụ cosine cao giữa 2 vector embedding nghĩa là 2 vector này có mức độ tương đòng cao -> thể hiện 2 câu này có ý nghĩa là tương đương nhau,

**Ví dụ có độ tương tự CAO:**
- Câu A: Hôm qua trời mưa
- Câu B: Hôm nay trời nắng
- Tại sao tương đồng: Cùng nói về chủ đề thời tiết

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hôm qua trời mưa
- Câu B: Hôm nay tôi đi bộ
- Tại sao khác: 2 câu đang nói về chủ đề khác nhau hoàn toàn: 1 chủ đề về thời tiết, 1 chủ đề về hành động

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity được ưu tiên hơn khoảng cách Euclid do cosine similarity sẽ không bị ảnh hưởng bởi độ dài văn bản và cosine similarity phân giải ngữ nghĩa của câu tốt hơn khoảng cách euclid
### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* ceil((10,000 - 50) / (500-50))
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Nếu overlap tăng lên 100 thì số lượng chunks sẽ là 25. Mức độ chồng chéo nhiều giúp các đoạn chunk được liên kết với nhau, tránh trường hợp truy xuất thiếu ngữ cảnh - lost in the middle giữa các đoạn chunk

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*
Dùng biểu thức chính quy: `re.compile(r'(?<=\.|\!|\?)(?:\s+|\n)')` để phát hiện câu, cần xử lý các trường hợp ngoại lệ như text rỗng, các đoạn sentences toàn kí tự khoảng trắng

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*
Thuật toán hoạt động bằng cách sử dụng đệ quy - lần lượt chia nhỏ đoạn văn theo thứ tự ưu tiên: từ kí tự \n\n phân tách từng đoạn section -> \n phân tách từng đoạn văn trong section đó -> sau đó đến từng đoạn dấu chấm, dấu phẩy. Trường hợp cơ sở là khi đoạn text nhỏ hơn hoặc bằng với chunk_size (không thể chia nhỏ được nữa) hoặc không còn kí tự để phân tách đoạn văn -> trả về đoạn text đó luôn
### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` dùng để lưu trữ tài liệu và vector embedding dưới dạng từ điển/danh sách các bản ghi chứa id, content, metadata và vector embedding. Khi tìm kiếm `search` sẽ tính độ tương tự cosine giữa vector truy vấn với từng vector trong danh sách thông qua công thức tính cosine similarity

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Nên áp dụng lọc trước để lọc các bản ghi thỏa mãn điều kiện metadata trước rồi mới tính độ tương tự vector-nhằm giảm tải tính toán và đảm bảo đủ top-k kết quả hợp lệ. Để xóa (delete_document), chỉ cần tìm theo khóa id của tài liệu và loại bỏ bản ghi tương ứng ra khỏi cấu trúc lưu trữ (hoặc đánh dấu deleted nếu dùng soft-delete).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
Cấu trúc prompt được thiết kế theo dạng template gồm 3 phần rõ gồm system_prompt,ngữ cảnh được truy xuất và câu hỏi của người dùng (Question). Ngữ cảnh được đưa vào bằng cách trích xuất nội dung văn bản từ các chunk trả về qua bước `search` hoặc `search_with_filter`, rồi nhúng trực tiếp vào vị trí context trước câu hỏi để LLM căn cứ trả lời.
---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
========================================================= test session starts ==========================================================
platform linux -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- /home/giap/Desktop/Workspace/Vin AI/K4-DAY07-NguyenVanGiap-2A202602903/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/giap/Desktop/Workspace/Vin AI/K4-DAY07-NguyenVanGiap-2A202602903
collected 42 items                                                                                                                     

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                            [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                     [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                              [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                               [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                    [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                    [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                          [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                           [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                         [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                           [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                           [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                      [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                  [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                            [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                   [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                       [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                 [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                       [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                           [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                             [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                               [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                     [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                          [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                            [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                             [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                      [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                     [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                            [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                       [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                           [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                 [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                           [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                        [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                      [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                     [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                         [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                    [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                             [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                   [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                       [100%]

========================================================== 42 passed in 0.04s ==========================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
