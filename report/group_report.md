# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3              |
| Tên nhóm         | B8     |
| Repository         | https://github.com/linhnguyenviet030704-oss/Day10_2A202601211_NguyenVietLinh |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Việt Linh | 2A202601211 | Phân công nhóm, chốt clean data schema và đánh giá result test | `report/README.md`, quy ước clean schema dùng chung, xác minh `tests/` |
| 2 | Lê Trần Khương Duy | 2A202601349 | LLM provider, Agent, Baseline pipeline & Observability (bước 7–11) | `src/retrieval/llm.py` (cấu hình), `src/pipelines/phase1.py`, `src/observability/quality.py`, `generate_phase1_report()` |
| 3 | Đỗ Tùng Dương | 2A202601899 | Corruption Simulation, Repair & Comparison Owner (bước 12–14) | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`, `generate_corruption_report()` |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành toàn bộ 2 pha của bài lab. Pha baseline (bước 1–11, do Linh và Duy phụ trách) lấy 24 record từ Crossref, làm sạch còn 22 record, build embedding index (MiniLM + ChromaDB) và đạt các chỉ số tối đa trên dữ liệu sạch: `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5.0`; 5/5 data quality check và freshness đều pass/fresh (`data/reports/phase1_report.md`).

Pha corruption (bước 12–14, do Dương phụ trách) tạo 5 loại lỗi có chủ đích trên dữ liệu sạch: drop 2 record mới nhất, blank 1 summary, inject noise vào 1 summary, truncate 1 title, làm cũ ngày publish của 1 record, và duplicate 1 record — khiến dataset còn 21 dòng. Corruption ảnh hưởng rõ rệt lên agent: `retrieval_hit_rate` giảm còn `0.6`, `mean_token_f1` còn `0.551`, `judge_accuracy` còn `0.467`, `mean_judge_score` còn `2.933`; quality check chuyển sang fail (`paper_id_unique`, `summary_present`, `summary_length_reasonable`) và freshness chuyển stale (1/21 record).

Repair bằng cách build lại dataset từ raw records gốc (`data/raw/crossref_records.json`) đã phục hồi hoàn toàn: cả 4 metric quay lại đúng baseline (1.0/1.0/1.0/5.0), quality và freshness đều pass/fresh trở lại (`data/reports/corruption_report.md`).

Giới hạn còn lại: (1) chưa xác nhận thống nhất `LLM_PROVIDER`/`LLM_MODEL` dùng chung giữa các thành viên khi chạy lại (mỗi người từng dùng provider khác nhau khi phát triển cục bộ — xem mục 4); (2) Ragas evaluation chưa được bật (`RUN_RAGAS=1`) trong lần chạy chính thức.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API | Fetch, retry 429/503, parse thành `PaperRecord` | `data/raw/` | Linh (chốt schema đầu vào) |
| Cleaning          | Raw records | Loại record thiếu field, dedupe theo `paper_id`, tính `age_days`, ghép `text_for_embedding` | `data/clean/papers_clean.csv`, `.json` | Linh (chốt clean schema dùng chung) |
| Embedding/index   | Cleaned DataFrame | MiniLM (`all-MiniLM-L6-v2`) + ChromaDB, 3 collection riêng cho baseline/corrupted/repaired | `data/embeddings/`, `data/chroma/` | Duy (baseline), Dương (corrupted/repaired) |
| Evaluation        | Cleaned DataFrame, index | 15 câu hỏi (summary/authors/date/…), token F1 + LLM judge | `data/eval/test_set.json`, `data/results/*_metrics.json` | Duy (baseline), Dương (corrupted/repaired) |
| Observability     | Cleaned DataFrame | 5 quality check (row count, `paper_id` unique, `title`/`summary` present, độ dài summary) + freshness theo `age_days` | `data/quality/*.json` | Duy |
| Corruption/repair | Baseline clean dataset + raw records | 5 loại corruption có log, repair bằng rebuild từ raw | `data/results/corruption_log.json`, `data/clean/*_corrupted.*`, `*_repaired.*` | Dương |
| Orchestration     | Toàn bộ module trên | `phase1.py`: 9 bước baseline; `corruption_flow.py`: corrupt → evaluate → repair → evaluate → compare | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Duy (`phase1.py`), Dương (`corruption_flow.py`) |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER` / `LLM_MODEL` | Chưa thống nhất tuyệt đối giữa các thành viên khi phát triển cục bộ (Duy dùng Gemini `gemini-flash-latest` sau khi model mặc định `gemini-2.5-flash` bị 404; Dương dùng OpenAI `gpt-4o-mini`) — nhóm cần chốt một cấu hình chung trước khi nộp bản cuối để đảm bảo số liệu tái lập được từ mọi máy |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `max_results = 24` (cấu hình mặc định trong `core/config.py`) |
| Retrieval `top_k`           | `4` |
| Freshness threshold          | `180 ngày` |
| Random seed, nếu có        | Không dùng random — corruption chọn record theo thứ tự cố định (mới nhất/theo index) để tái lập được giữa các lần chạy |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | `data/reports/phase1_report.md`, `data/results/baseline_metrics.json` |
| Corruption flow   | Thành công | 2026-08-06 | `data/reports/corruption_report.md`, `data/results/corruption_log.json` |

Ngoài ra Linh đã xác minh riêng phần test suite: `uv run --with pytest python -m pytest -q` pass `18/18`; chạy trực tiếp `python -m pytest -q` trên Python 3.14 (ngoài khoảng `>=3.11,<3.14` mà `pyproject.toml` yêu cầu) bị lỗi môi trường chứ không phải lỗi logic (xem `report/linh_report.md` mục 6).

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter                | `query="agentic retrieval augmented generation large language model"`, `filter=from-pub-date:<180 ngày trước>,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được    | 24 raw records, còn 22 sau cleaning |
| Cơ chế retry/backoff      | Retry tối đa 3 lần khi HTTP 429/503 hoặc `URLError`, backoff tuyến tính |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` (DOI) | string | Có | Định danh duy nhất của paper | Record bị loại nếu rỗng |
| `title` | string | Có | Tiêu đề bài báo | Record bị loại nếu rỗng |
| `summary` | string | Có | Abstract đã strip HTML tag | Record bị loại nếu rỗng |
| `authors`, `categories` | list[string] | Không | Metadata gốc | Giữ list rỗng nếu thiếu |
| `published` | date (`YYYY-MM-DD`) | Có | Ngày công bố, dùng cho freshness | Record bị loại nếu không parse được ngày |
| `age_days` | int | Có (tính ở bước clean) | Số ngày từ `published` đến lúc chạy pipeline | Tính lại từ `published_at` và `run_date` |
| `text_for_embedding` | string | Có (tính ở bước clean) | Text ghép title/summary/authors/categories/published để embed | Rebuild lại nếu bất kỳ trường nguồn nào thay đổi (kể cả khi corrupt) |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record thiếu `paper_id`/`title`/`summary`/ngày publish hợp lệ | Completeness |  2 (24 raw → 22 clean) | So `data/raw/crossref_records.json` với `data/clean/papers_clean.json` |
| Dedupe theo `paper_id` (giữ bản mới nhất theo `published`) | Uniqueness | 0 trong baseline | Check `paper_id_unique` trong `data/quality/baseline_quality.json` |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`text_for_embedding` ghép các dòng `Title:`, `Summary:`, `Authors:`, `Categories:`, `Published:` (và `Venue:` nếu có) nối bằng newline. Document ID chính là `paper_id` (DOI từ Crossref), giữ nguyên xuyên suốt raw → clean → corrupted → repaired để `ground_truth_doc_ids` trong evaluation set luôn tham chiếu đúng — đây là schema do Linh chốt và các module khác (quality, retrieval, corruption) dùng chung không transform lại. `age_days` = số ngày giữa thời điểm chạy pipeline và `published`, dùng trực tiếp cho freshness check với ngưỡng 180 ngày.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 15 (5 paper mới nhất × 3 câu hỏi/paper) |
| Các `question_type`                    | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID                 | Chính là `paper_id` (DOI) của paper nguồn câu hỏi |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB, 3 collection riêng cho baseline/corrupted/repaired |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | Xem ghi chú ở mục 4 (chưa thống nhất tuyệt đối giữa các thành viên) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` — chỉ tạo một lần ở baseline, không refresh khi chạy corruption flow |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

`phase1.py` chỉ tạo test set nếu `data/eval/test_set.json` chưa tồn tại; `corruption_flow.py` dùng lại đúng file này cho cả 3 lần evaluate. Nhờ vậy chênh lệch giữa các metric baseline/corrupted/repaired phản ánh đúng ảnh hưởng của thay đổi dữ liệu, không lẫn với việc bộ câu hỏi bị đổi — đây là điều kiện tiên quyết cả Duy và Dương đều tuân thủ khi ghép orchestration.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | `crossref_response.json` + `crossref_records.json`, 24 record |
| Cleaned dataset          | `data/clean/`                        | Có | `papers_clean.csv`/`.json`, 22 record |
| Embedding manifest/index | `data/embeddings/`                   | Có | `papers_embeddings.json` + ChromaDB persist tại `data/chroma/` |
| Evaluation set           | `data/eval/`                         | Có | `test_set.json`, 15 câu hỏi |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Xem bảng bên dưới |
| Quality/freshness        | `data/quality/`                      | Có | `baseline_quality.json`, `freshness_report.json` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Markdown đầy đủ |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | Top-k luôn chứa đúng `paper_id` ground truth trên dữ liệu sạch |
| `mean_token_f1`      |     1.0 | Answer trích xuất khớp hoàn toàn ground truth |
| `judge_accuracy`     |     1.0 | LLM judge đồng ý toàn bộ 15/15 câu trả lời là đúng |
| `mean_judge_score`   |     5.0 | Điểm tối đa trên thang 1-5 |
| Ragas, nếu có        | N/A (skipped) | `RUN_RAGAS` chưa bật trong lần chạy chính thức |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count_positive` | Completeness | > 0 dòng | Pass (`22`) | `data/quality/baseline_quality.json` |
| `paper_id_unique` | Uniqueness | Không trùng lặp | Pass (`22/22`) | `data/quality/baseline_quality.json` |
| `title_present` | Completeness | Không rỗng | Pass (`22/22`) | `data/quality/baseline_quality.json` |
| `summary_present` | Completeness | Không rỗng | Pass (`22/22`) | `data/quality/baseline_quality.json` |
| `summary_length_reasonable` | Validity | ≥ 40 ký tự | Pass (trung bình `1777.5` ký tự) | `data/quality/baseline_quality.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cleaned DataFrame (22 record) |
| Timestamp mới nhất       | `latest_published = 2026-08-01` |
| Ngưỡng freshness         | 180 ngày |
| Trạng thái baseline      | Fresh (`is_fresh: true`, `stale_rows: 0`) |
| Lý do                     | Record được lấy với filter `from-pub-date:<180 ngày trước>`, nên `age_days` luôn ≤ ngưỡng |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop latest records | Xóa 2 record có `published` mới nhất | 2 | Giảm coverage, mất document mà evaluation set tham chiếu | `retrieval_hit_rate` giảm mạnh (1.0 → 0.6) | Rebuild từ `data/raw/crossref_records.json` |
| Blank summary | Set `summary = ""` trên 1 record | 1 | Fail `summary_present` | `summary_present`: `19/21` | Rebuild từ raw |
| Summary noise | Thêm token nhiễu vào đầu summary | 1 | Giảm chất lượng embedding/answer | Góp phần giảm `mean_token_f1` xuống 0.551 | Rebuild từ raw |
| Truncate title | Cắt ngắn `title` | 1 | Không ảnh hưởng check hiện tại (giới hạn đã ghi ở mục 12) | Có thể ảnh hưởng câu hỏi dạng "Summarize the paper '...'" nếu match theo title | Rebuild từ raw |
| Stale published date | Đẩy `published` về quá khứ (>400 ngày) | 1 | Fail `freshness` | `is_fresh: false`, `stale_rows: 1/21` | Rebuild từ raw (dùng lại `published` gốc) |
| Duplicate row | Nhân đôi 1 record | 1 | Fail `paper_id_unique` | `paper_id_unique`: `20/21` | Rebuild từ raw (dedupe theo `paper_id`) |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log liệt kê đầy đủ các hành động corruption kèm `paper_id` bị ảnh hưởng; `final_row_count: 21` (từ 22 record baseline, drop 2 + duplicate 1).

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

`corruption_flow.py` không sửa trực tiếp `corrupted_df` (không "un-blank" summary hay xóa duplicate thủ công). Thay vào đó, bước repair đọc lại `data/raw/crossref_records.json` (raw records gốc, chưa từng bị corrupt) và chạy lại đúng hàm `build_clean_dataframe()` giống bước cleaning ở baseline. Vì vậy repaired dataset độc lập hoàn toàn với các thay đổi đã áp vào corrupted dataset — đây là phục hồi từ nguồn đáng tin cậy, không phải vá kết quả lỗi.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |     1.000 |     0.600 |     1.000 |                  -0.400 |            +0.400 | Giảm nhiều nhất — drop 2 record mới nhất trực tiếp xóa ground-truth doc khỏi index |
| `mean_token_f1`        |     1.000 |     0.551 |     1.000 |                 -0.449 |           +0.449 | Giảm theo do answer bị lấy từ record sai hoặc summary rỗng/nhiễu |
| `judge_accuracy`       |     1.000 |     0.467 |     1.000 |                 -0.533 |           +0.533 | LLM judge đồng thuận với token F1, phần lớn câu trả lời trên dữ liệu corrupted bị đánh giá sai |
| `mean_judge_score`     |     5.000 |     2.933 |     5.000 |                 -2.067 |           +2.067 | Điểm trung bình giảm hơn một nửa, phục hồi hoàn toàn sau repair |
| Quality checks pass/fail |      pass |       fail |      pass |         3/5 check chuyển fail (`paper_id_unique`, `summary_present`, `summary_length_reasonable`) | Phục hồi toàn bộ | Quality check phát hiện đúng 3/5 loại corruption có tín hiệu ở tầng dòng dữ liệu |
| Freshness status         |     fresh |      stale |      fresh |                  +1 stale row | Phục hồi toàn bộ | Đúng bằng 1 record bị "stale date" trong corruption log |

Hai kết luận nhân quả được hỗ trợ bởi artifact:

1. **Corruption** (drop 2 record mới nhất + duplicate 1 record + blank/noise summary + stale date) → **quality/freshness signal thay đổi** (`corrupted_quality.json`: `passed=false`, 3/5 check fail; `corrupted_freshness_report.json`: `is_fresh=false`, `stale_rows=1`) → **retrieval/answer metric giảm mạnh** (`retrieval_hit_rate` 1.0→0.6, `judge_accuracy` 1.0→0.467, theo `corrupted_metrics.json`).
2. **Repair** (build lại từ `crossref_records.json` bằng đúng `build_clean_dataframe()`) → **quality/freshness signal phục hồi hoàn toàn** (`repaired_quality.json`: `passed=true`; `repaired_freshness_report.json`: `is_fresh=true`) → **agent metric phục hồi hoàn toàn về baseline** (`repaired_metrics.json` bằng đúng `baseline_metrics.json`: 1.0/1.0/1.0/5.0).

Không có kết quả nào khác với kỳ vọng — corruption có tác động rõ ràng và nhất quán trên cả 4 metric, và repair phục hồi hoàn toàn (100%) trên toàn bộ metric đo được.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** `.env` mặc định trỏ tới `gemini-2.5-flash`, khi Duy gọi thực tế bị lỗi `404 NOT_FOUND` (model đã bị Google gỡ cho key mới).
- **Nguyên nhân:** Model snapshot `gemini-2.5-flash` không còn được cấp cho API key mới; đây là lỗi model bị deprecate (404), không phải lỗi credential (401/403).
- **Cách xử lý:** Duy đổi `LLM_MODEL` sang alias `gemini-flash-latest` để tránh lỗi model bị gỡ và tránh rate-limit `429` khi chạy nhiều lời gọi judge liên tiếp.
- **Cách xác minh:** Live-call `build_llm(settings).invoke(...)` trả về đúng kết quả; baseline chạy 15/15 sample judge không lỗi (`judge_accuracy = 1.0`); corruption flow chạy tiếp 30 lời gọi judge (corrupted + repaired) hoàn tất không lỗi.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Chưa thống nhất `LLM_PROVIDER`/`LLM_MODEL` dùng chung giữa các thành viên | Số liệu có thể lệch nhẹ giữa các lần chạy trên máy khác nhau (đã thấy sai khác giữa các báo cáo cá nhân trước khi đối chiếu lại với artifact thật) | Chốt 1 provider/model trong `.env.example` và ghi rõ trong `group_report.md`, chạy lại 1 lần cuối trước khi nộp để đồng bộ toàn bộ artifact |
| Không có quality check riêng cho `title` bị truncate | Corruption "truncate_title" không được `run_data_quality_checks` phát hiện | Thêm check `title_min_length` tương tự `summary_length_reasonable` |
| Ragas evaluation mặc định bị skip (`RUN_RAGAS` chưa bật) | Thiếu metric answer_relevancy/context_precision/recall/faithfulness trong báo cáo | Bật `RUN_RAGAS=1` khi chạy lại lần cuối và so sánh thêm các Ragas metric giữa 3 trạng thái |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp (theo xác minh của Linh và Dương).
- [x] Baseline, corrupted và repaired dùng cùng evaluation set (`data/eval/test_set.json`).
- [x] Bảng metrics khớp với các file trong `data/results/` (đối chiếu trực tiếp `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`).
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng (`report/linh_report.md`, `report/duy_report.md`, `report/2A202601899_DoTungDuong.md`).
- [ ] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh — cần rà soát lần cuối trước khi nộp vì mỗi thành viên từng dùng `.env` cục bộ khác nhau (đã xác nhận `.env` nằm trong `.gitignore`, nhưng nên kiểm tra lại lịch sử commit của cả 3 nhánh trước khi merge).
