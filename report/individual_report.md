# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                                     |
| ------------------ | --------------------------------------------------------------------------------------------- |
| Họ và tên       | Lê Trần Khương Duy                                                                        |
| MSSV               | 2A202601349                                                                                    |
| Khóa/Lớp         | K3                                                                                             |
| Tên nhóm         | B8                                                                                             |
| Vai trò chính    | LLM provider, Agent, Baseline pipeline & Observability (bước 7–11)                          |
| Repository         | https://github.com/linhnguyenviet030704-oss/Day10_2A202601211_NguyenVietLinh (branch: `duy`) |
| Ngày hoàn thành | 2026-08-06                                                                                     |

## 2. Vai trò và phạm vi công việc

Phạm vi của tôi là **bước 7–11** trong `Guide.md`: cấu hình LLM provider, chạy/kiểm chứng agent, hoàn thiện baseline pipeline, đọc score và xây dựng lớp data observability (quality + freshness + báo cáo pha 1).

### Phần việc sở hữu

| Module/deliverable                | File/hàm phụ trách                                                                          | Input nhận vào                             | Output bàn giao                                                             | Trạng thái     |
| --------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------- | ---------------- |
| LLM provider (bước 7)            | `src/retrieval/llm.py` (starter) + cấu hình `.env`                                        | `LLM_PROVIDER`, `LLM_MODEL`, API key         | Provider Gemini chạy được, đã verify bằng lời gọi thực                | Hoàn thành    |
| Agent (bước 8)                   | `src/retrieval/agent.py`, `src/retrieval/qa.py` (starter)                                   | Vector index, câu hỏi                      | Agent trả lời factual qua `semantic_search_papers` + `lookup_paper`        | Hoàn thành    |
| Baseline pipeline (bước 9)       | `src/pipelines/phase1.py` (tôi implement)                                                    | Raw records, clean df, test set              | `baseline_metrics.json`, `baseline_answers.json`, `phase1_report.md`         | Hoàn thành    |
| Đọc score (bước 10)            | `data/results/baseline_metrics.json`                                                          | Metrics JSON                                 | Diễn giải 4 chỉ số chính + trạng thái quality/freshness                 | Hoàn thành    |
| Data quality & freshness (bước 11) | `src/observability/quality.py` (tôi implement)                                              | Clean/corrupted/repaired df                  | `*_quality.json`, `freshness_report*.json`                                   | Hoàn thành    |
| Reporting pha 1 (bước 11)       | `generate_phase1_report()` trong `src/observability/reporting.py` (tôi implement)            | source summary, metrics, quality, freshness  | `data/reports/phase1_report.md`                                              | Hoàn thành    |

Ghi chú trung thực về ownership:

- `llm.py`, `agent.py`, `qa.py` là **code tham khảo có sẵn của starter**. Phần việc thực tế của tôi ở bước 7–8 là *cấu hình provider, sửa model, và kiểm chứng* chứ không viết lại code này.
- `phase1.py`, `quality.py` và hàm `generate_phase1_report` trong `reporting.py` là phần **tôi trực tiếp implement** từ stub `NotImplementedError`.
- Hàm `generate_corruption_report`, `corruption.py` và `corruption_flow.py` (bước 12–14) **không thuộc phạm vi của tôi** — do thành viên phụ trách corruption/integration sở hữu.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                                                      | Thành viên/module được hỗ trợ         | Kết quả                                                                 |
| ----------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------ |
| Cung cấp `run_data_quality_checks`/`build_freshness_report` để corruption flow tái sử dụng | Module `corruption_flow.py`                 | Corrupted/repaired dùng lại đúng cùng bộ check, ra `*_quality.json` |
| Kiểm tra vệ sinh secret trước khi nộp                        | Cả nhóm                                    | Xác nhận `.env` bị `.gitignore`, không có key trong Git/report        |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                       | File/hàm/artifact liên quan                     | Kết quả bàn giao                                          | Cách xác minh                              |
| ------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| Sửa model Gemini bị lỗi, verify provider       | `.env`, `src/retrieval/llm.py`                    | Provider Gemini gọi được, trả `OK`                     | Live-call qua `build_llm(...).invoke(...)`  |
| Chạy agent trên corpus đã index                | `src/retrieval/agent.py`, `qa.py`                 | Agent tóm tắt/lookup đúng paper                          | Semantic search + summary "SafeRAG" đúng   |
| Orchestrate baseline end-to-end                   | `src/pipelines/phase1.py`                          | 22 clean rows, 15 test samples, metrics + report            | `python script/run_phase1.py` (exit 0)      |
| Data quality checks (6 check) + freshness         | `src/observability/quality.py`                     | `baseline_quality.json` PASS, `freshness_report.json` FRESH | Đọc artifact trong `data/quality/`         |
| Báo cáo Markdown pha 1                          | `generate_phase1_report()`                         | `data/reports/phase1_report.md`                             | Mở file, đối chiếu với metrics JSON      |

Một output cụ thể: `data/reports/phase1_report.md` gộp source summary, metrics, 6 data-quality checks (PASS) và freshness (FRESH, 22/22 row trong ngưỡng 180 ngày), được sinh trực tiếp từ artifact thật của lần chạy baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Bước 7–8 cần một agent RAG gọi LLM được và truy hồi đúng từ corpus. Bước 9–11 cần biến các module rời rạc (ingestion, cleaning, index, evaluation) thành **một baseline pipeline chạy một lệnh** và gắn thêm lớp **observability** để phát hiện dữ liệu xấu *trước khi* người dùng nhận câu trả lời sai.

### Cách triển khai

- **LLM provider (bước 7):** `build_llm` map `LLM_PROVIDER` → client tương ứng và validate credential qua `require_llm_credentials`. Việc của tôi là chọn model hợp lệ và verify (xem mục 6).
- **Agent (bước 8):** agent dùng 2 tool — `semantic_search_papers` (truy vấn ChromaDB top-k) và `lookup_paper` (tra cứu chính xác theo `paper_id`/title). Tôi kiểm chứng cả nhánh agent (LLM + tool) lẫn nhánh `answer_question` tất định.
- **Baseline pipeline (bước 9):** `phase1.py` điều phối tuần tự: load/fetch raw → `build_clean_dataframe` → `LocalEmbeddingIndex.build` → load/tạo test set → `evaluate_pipeline` → `run_data_quality_checks` + `build_freshness_report` → `generate_phase1_report`. Có guard `refresh_source`/`refresh_test_set` và fail sớm nếu không có clean row.
- **Quality checks (bước 11):** 6 check độc lập — row count > 0, `paper_id` không rỗng, `paper_id` unique, `title` không rỗng, `summary` ≥ 40 ký tự, và freshness (có ít nhất một row trong ngưỡng). Kết quả tổng hợp thành `success = (không có check nào fail)`.
- **Freshness report:** tính `latest/oldest_published`, `stale_rows` (`age_days > threshold`), `is_fresh = (stale_rows == 0 and fresh_rows > 0)`.
- **Report pha 1:** render Markdown gồm bảng source, bảng metrics, bảng từng check quality và bảng freshness.

### Input, output và contract

| Thành phần                   | Mô tả                                                                                                   |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Input                          | `list[PaperRecord]` (raw), `DataFrame` clean schema (`paper_id, title, summary, ..., age_days, text_for_embedding`) |
| Output                         | `baseline_metrics.json`, `baseline_answers.json`, `*_quality.json`, `freshness_report.json`, `phase1_report.md` |
| Module phụ thuộc             | `ingestion.cleaning`, `retrieval.index`, `evaluation.metrics` (không đổi chữ ký hàm dùng chung)      |
| Module sử dụng output        | `pipelines.corruption_flow` tái dùng `run_data_quality_checks`/`build_freshness_report`                 |
| Điều kiện lỗi cần xử lý | Clean df rỗng (raise sớm); LLM judge lỗi/rate-limit (fallback heuristic trong `metrics.py`); model retired (đổi model) |

### Cách xác minh

```bash
python script/run_phase1.py
python -m pytest -q
```

- **Kết quả mong đợi:** pipeline chạy hết, sinh đủ artifact baseline; test suite pass.
- **Kết quả thực tế:** `run_phase1.py` exit 0 — hit_rate 1.0, token_f1 1.0, judge_accuracy 1.0, judge_score 5; quality PASS (6/6); freshness FRESH. `pytest` → 7 passed.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/quality/baseline_quality.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** `.env` mặc định trỏ tới `gemini-2.5-flash`, khi gọi thực tế bị 404 (model đã bị gỡ cho key mới). Cần chọn model thay thế cho toàn bộ pipeline (baseline + judge).
- **Các phương án đã cân nhắc:**
  1. Pin `gemini-2.0-flash` — gọi được nhưng gặp `429 RESOURCE_EXHAUSTED` do rate limit free-tier.
  2. Dùng alias `gemini-flash-latest` — luôn trỏ tới model flash hiện hành, gọi được ngay.
- **Phương án đã chọn:** `LLM_MODEL=gemini-flash-latest`.
- **Lý do:** tránh đúng lỗi "model retired" vừa gặp và không bị 429 khi chạy 15+ lời gọi judge; trade-off là kém tái lập tuyệt đối hơn bản pin (alias có thể đổi model bên dưới), nhưng với bài lab dùng chung một cấu hình cho cả 3 trạng thái thì so sánh vẫn hợp lệ.
- **Bằng chứng quyết định phù hợp:** baseline chạy 15/15 sample judge không lỗi, `judge_accuracy = 1.0`; corruption flow chạy 30 lời gọi judge (corrupted + repaired) hoàn tất, exit 0.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `google.genai.errors.ClientError: 404 NOT_FOUND ... This model models/gemini-2.5-flash is no longer available to new users.` (API key đã che, chỉ hiện prefix `AQ.Ab8…`).
- **Lệnh hoặc bước tái hiện:** `build_llm(settings).invoke("Reply with exactly: OK")` với `LLM_MODEL=gemini-2.5-flash`.
- **Nguyên nhân gốc:** không phải sai key (request đã qua bước xác thực, lỗi là 404 chứ không phải 401/403); model snapshot `gemini-2.5-flash` đã bị Google ngừng cấp cho API key mới.
- **Cách xử lý:** đổi dòng `LLM_MODEL` trong `.env` sang `gemini-flash-latest`.
- **Cách xác minh sau khi sửa:** live-call trả về `OK`; liệt kê model khả dụng bằng `client.models.list()` xác nhận `gemini-flash-latest` và `gemini-3.5-flash` gọi được, `gemini-2.0-flash` bị 429.
- **Điều học được:** không pin cứng model snapshot dễ bị deprecate; nên verify khả dụng bằng `models.list()` và ưu tiên alias `*-latest`. Đọc kỹ mã lỗi (404 vs 401) để phân biệt lỗi model với lỗi credential.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Crossref → vector index:** `crossref.py` gọi REST API, lưu raw response + parse thành `PaperRecord` (`data/raw/`). `cleaning.py` chuẩn hóa, khử trùng lặp theo `paper_id`, lọc row thiếu, tính `age_days` và ghép `text_for_embedding`. `index.py` encode `text_for_embedding` bằng MiniLM và nạp vào collection ChromaDB (cosine).
2. **Evaluation set & ground-truth IDs:** `testset.py` sinh câu hỏi (summary/authors/date/…) từ top-5 paper mới nhất; mỗi sample có `ground_truth` và `ground_truth_doc_ids`. `retrieval_hit_rate` đo xem doc đúng có nằm trong top-k truy hồi không; `token_f1` và LLM judge đo chất lượng câu trả lời so với ground truth.
3. **Quality vs freshness:** data quality kiểm *tính toàn vẹn cấu trúc* (null/unique/độ dài summary), còn freshness kiểm *độ mới theo thời gian* (`age_days` so với ngưỡng 180 ngày). Một dataset có thể "sạch" về cấu trúc nhưng vẫn "stale".
4. **Cùng test set cho 3 trạng thái:** chỉ khi baseline, corrupted và repaired được đo trên *cùng* evaluation set thì chênh lệch metric mới phản ánh tác động của chất lượng dữ liệu, chứ không phải do đổi câu hỏi.
5. **Repair thành công dựa trên:** `repaired_metrics.json` quay lại mức baseline (hit_rate 1.0, f1 1.0, judge 1.0/5), `repaired_quality.json` PASS và `freshness_report_repaired.json` FRESH — nghĩa là dựng lại từ raw đã khôi phục cả metric lẫn tín hiệu observability.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                                              |
| ---------------------- | -------: | --------: | -------: | ------------------------------------------------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.4000 |   1.0000 | Drop 3 paper mới nhất (đều thuộc test set) làm miss 9/15 sample |
| `mean_token_f1`      |   1.0000 |    0.2947 |   1.0000 | Blank summary + truy hồi sai kéo overlap token xuống mạnh        |
| `judge_accuracy`     |   1.0000 |    0.2667 |   1.0000 | LLM judge đánh phần lớn câu trả lời corrupted là sai           |
| `mean_judge_score`   |   5.0000 |    2.0667 |   5.0000 | Điểm chất lượng trung bình rớt hơn một nửa                   |
| Quality checks         |     PASS |      FAIL |     PASS | Corrupted fail `paper_id_unique` (duplicate) và `summary_min_length` (blank) |
| Freshness status       |    FRESH |     STALE |    FRESH | 2 row bị đẩy về 2005 → `is_fresh=false` (2 stale / 21 row)   |

### Kết luận từ số liệu

1. **Data corruption** (drop latest + blank summary + stale date + duplicate) → **quality FAIL + freshness STALE** → **agent metric tụt** (hit 1.0 → 0.4, judge_score 5 → 2.07).
2. **Repair** (dựng lại clean từ `data/raw/`) → **quality PASS + freshness FRESH trở lại** → **agent metric phục hồi hoàn toàn** về mức baseline (1.0/1.0/1.0/5).

Corruption ảnh hưởng rõ nhất là **drop 3 record mới nhất**: vì test set lấy từ top-5 paper mới nhất, việc bỏ 3 paper này xóa thẳng ground-truth doc khỏi index, kéo `retrieval_hit_rate` từ 1.0 về 0.4 (9/15 sample miss) — tác động mạnh hơn hẳn blank/noise vốn chỉ hạ chất lượng câu trả lời.

Kết quả khác kỳ vọng: **stale date và duplicate gần như không làm đổi metric eval** (vì rơi vào paper ngoài test set), nhưng **vẫn bị quality/freshness bắt được**. Điều này khớp thông điệp của lab: chỉ nhìn metric agent là chưa đủ, observability bắt được lỗi mà eval bỏ sót.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** đóng gói ETL + index + eval sau một entrypoint (`phase1.py`) giúp tái lập; guard đầu vào (clean df rỗng) tránh lỗi mơ hồ ở bước sau.
2. **Data quality/observability:** quality (cấu trúc) và freshness (thời gian) là hai trục *độc lập*; cần cả hai vì một dataset có thể pass cái này mà fail cái kia.
3. **Ảnh hưởng data → RAG agent:** chất lượng dữ liệu tác động trực tiếp và đo được lên metric; đặc biệt lỗi ở đúng tập ground-truth (drop latest) gây hại nặng nhất cho retrieval.

### Nếu có thêm thời gian

Tôi sẽ thêm **check chống drift giữa test set và index** — cảnh báo khi `ground_truth_doc_ids` không còn tồn tại trong collection — và đo cải thiện bằng số sample bị miss "im lặng" được phát hiện sớm thay vì chỉ thấy qua `retrieval_hit_rate` tụt.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Trần Khương Duy
**Ngày xác nhận:** 2026-08-06
