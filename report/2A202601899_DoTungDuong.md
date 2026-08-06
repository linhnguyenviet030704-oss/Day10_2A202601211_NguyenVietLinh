# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                                                    |
| ------------------ | -------------------------------------------------------------------------------------------------------------- |
| Họ và tên       | Đỗ Tùng Dương                                                                                             |
| MSSV               | 2A202601899                                                                                                    |
| Khóa/Lớp         | K3                                                                                                              |
| Tên nhóm         | B8                                                                                                              |
| Vai trò chính    | Corruption Simulation, Repair & Comparison Owner (bước 12–14)                                                |
| Repository         | https://github.com/linhnguyenviet030704-oss/Day10_2A202601211_NguyenVietLinh (branch: `duong`)                  |
| Ngày hoàn thành | 2026-08-06                                                                                                      |

## 2. Vai trò và phạm vi công việc

Phạm vi của tôi là **bước 12–14** trong `Guide.md`: giả lập data corruption có chủ đích, ghép flow re-evaluate sau corruption (rebuild index → evaluate → quality/freshness → repair từ raw → evaluate lại), và tạo comparison report so sánh baseline/corrupted/repaired.

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ------------ |
| Corruption simulation (bước 12) | `src/ingestion/corruption.py` — `corrupt_clean_dataframe()` (tôi implement) | Cleaned baseline DataFrame (schema do Nguyễn Việt Linh chốt) | Corrupted DataFrame + `data/results/corruption_log.json` | Hoàn thành |
| Corruption/repair orchestration (bước 13) | `src/pipelines/corruption_flow.py` — `main()` (tôi implement) | Baseline artifacts (`baseline_metrics.json`, `papers_clean.json`), raw records | Corrupted/repaired dataset, `corrupted_metrics.json`, `repaired_metrics.json`, `corrupted_answers.json`, `repaired_answers.json` | Hoàn thành |
| Comparison report (bước 14) | `generate_corruption_report()` trong `src/observability/reporting.py` (tôi implement) | baseline/corrupted/repaired metrics + quality + freshness dict | `data/reports/corruption_report.md` | Hoàn thành |

Ghi chú trung thực về ownership:

- `src/pipelines/phase1.py`, `src/observability/quality.py` (`run_data_quality_checks`, `build_freshness_report`) và `generate_phase1_report()` **không thuộc phạm vi chính của tôi** — thuộc bước 7–11, do Lê Trần Khương Duy sở hữu. Trong `corruption_flow.py` tôi chỉ **gọi lại** các hàm này (đúng contract có sẵn) để chạy quality/freshness check trên dữ liệu corrupted/repaired, không viết lại logic bên trong.
- **Ngoại lệ duy nhất:** sau khi phát hiện qua bước 12–14 rằng `truncate_title` (1 trong 6 loại corruption tôi tạo) không bị `run_data_quality_checks()` phát hiện, tôi có bổ sung thêm 1 check nhỏ `title_min_length` vào `src/observability/quality.py` (không đổi chữ ký hàm, không đụng logic 6 check còn lại của Duy) để bộ quality checks bắt đủ tín hiệu cho corruption tôi tạo ra — đã trao đổi và được Duy đồng ý trước khi thêm.
- `crossref.py`, `cleaning.py`, `testset.py`, `retrieval/*` là code/starter đã có sẵn, không phải phần tôi implement, nhưng tôi đọc kỹ contract (schema `PaperRecord`, cột `text_for_embedding`, cách `LocalEmbeddingIndex` đặt tên collection theo đường dẫn embeddings) để `corruption_flow.py` gọi đúng thứ tự và không phá dữ liệu của các bước trước.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------ | -------------------------------- | ---------- |
| Cài đặt môi trường (`.venv`, `pip install -e .`, `.env`) trên máy cá nhân để tái hiện toàn bộ flow | Toàn bộ pipeline | Chạy lại được `run_phase1.py` rồi `run_corruption_flow.py` end-to-end trên máy riêng, không chỉ dựa vào artifact có sẵn trong repo |
| Chạy lại `run_data_quality_checks`/`build_freshness_report` của Duy trên corrupted/repaired dataset để kiểm tra contract có khớp không | `src/observability/quality.py` | Xác nhận 2 hàm nhận đúng DataFrame do `corrupt_clean_dataframe()` sinh ra mà không cần sửa chữ ký hàm |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------- | --------------- |
| Viết corruption với 6 loại lỗi có chủ đích (drop latest, blank summary, noise injection, truncate title, stale date, duplicate rows), rebuild lại `text_for_embedding` sau khi corrupt | `src/ingestion/corruption.py` | `data/results/corruption_log.json`: 22 → 21 record, 6 nhóm hành động, liệt kê đúng `paper_id` bị ảnh hưởng | `python script/run_corruption_flow.py` rồi đọc file JSON |
| Ghép corruption flow: đọc baseline → corrupt → rebuild index (`papers-corrupted`) → evaluate trên cùng test set → quality/freshness → repair từ raw (`papers-repaired`) → evaluate lại → comparison report | `src/pipelines/corruption_flow.py` | `retrieval_hit_rate` giảm còn `0.4`, sau repair quay lại `1.0` | `python script/run_corruption_flow.py` |
| Viết markdown report so sánh 3 trạng thái (bảng metrics, bảng quality, bảng freshness, phần phân tích chênh lệch) | `generate_corruption_report()` trong `src/observability/reporting.py` | `data/reports/corruption_report.md` | Mở file, đối chiếu với `data/results/*_metrics.json` |

Output cụ thể: `data/results/corruption_log.json` ghi rõ 3 record bị drop, 3 record bị blank summary, 3 record bị inject noise, 3 record bị truncate title, 3 record bị đẩy `published` về `2015-01-01`, và 2 record bị duplicate — tổng cộng dataset đi từ 22 xuống 21 dòng (drop 3, duplicate lại 2).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Bước 12–14 phải trả lời được: (1) làm sao mô phỏng lỗi dữ liệu thực tế một cách có kiểm soát (không phá hủy toàn bộ dataset, vẫn đo được), và (2) làm sao chứng minh bằng số liệu — trên cùng một evaluation set — rằng corruption làm giảm chất lượng agent và repair từ raw source phục hồi được, chứ không phải "chạy xong là coi như xong".

### Cách triển khai

- `corrupt_clean_dataframe()` nhận cleaned DataFrame của baseline (schema đã được Nguyễn Việt Linh chốt: `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `age_days`, `text_for_embedding`, ...), áp 6 phép biến đổi theo slice cố định (không random) để **tái lập được** giữa các lần chạy: drop 1/6 record mới nhất theo `published`, sau đó chia phần còn lại thành các slice liên tiếp cho blank/noise/truncate/stale, cuối cùng duplicate 2 record đầu.
- Sau khi sửa các cột gốc, hàm **rebuild lại** `authors_joined`, `categories_joined`, `summary_chars` và đặc biệt là `text_for_embedding` — nếu bỏ bước này, ChromaDB vẫn index trên text cũ (chưa corrupt) và corruption sẽ "vô hình" với retrieval.
- `corruption_flow.py` đóng vai trò orchestration thuần: guard đầu vào (raise lỗi rõ ràng nếu chưa có `baseline_metrics.json`/`clean_json`), sau đó gọi tuần tự `corrupt_clean_dataframe()` → `LocalEmbeddingIndex.build()` (collection `papers-corrupted`) → `evaluate_pipeline()` trên **đúng** `data/eval/test_set.json` đã dùng ở baseline → `run_data_quality_checks()`/`build_freshness_report()` (hàm của Duy) → repair bằng cách đọc lại `data/raw/crossref_records.json` và gọi lại `build_clean_dataframe()` (hàm có sẵn, không sửa) → `LocalEmbeddingIndex.build()` (collection `papers-repaired`) → evaluate lại → `generate_corruption_report()`.
- Điểm mấu chốt: **repair = rebuild từ raw, không sửa trực tiếp `corrupted_df`**. Tôi không "un-blank" summary hay xóa duplicate thủ công trên dữ liệu đã corrupt — thay vào đó dựng lại hoàn toàn từ nguồn gốc (raw records chưa từng bị corrupt), đúng tinh thần "repair từ nguồn đáng tin cậy" mà rubric yêu cầu.

### Input, output và contract

| Thành phần | Mô tả |
| ------------ | ------- |
| Input | `Settings` (`core/config.py`), `baseline_metrics.json`, `papers_clean.json`, `crossref_records.json` |
| Output | `corruption_log.json`, corrupted/repaired CSV+JSON, `corrupted_metrics.json`, `repaired_metrics.json`, `corrupted_answers.json`, `repaired_answers.json`, `corruption_report.md` |
| Module phụ thuộc | `ingestion.cleaning` (`build_clean_dataframe`), `ingestion.crossref` (`load_raw_records`), `retrieval.index` (`LocalEmbeddingIndex`), `evaluation.metrics` (`evaluate_pipeline`), `observability.quality` (hàm của Duy) |
| Module sử dụng output | `script/run_corruption_flow.py`; `report/group_report.md` dùng số liệu trong `data/results/`, `data/reports/corruption_report.md` để tổng hợp |
| Điều kiện lỗi cần xử lý | Chưa chạy `run_phase1.py` trước (thiếu `baseline_metrics.json`/`clean_json`) → raise `RuntimeError` rõ ràng ngay đầu `main()`, tránh lỗi mơ hồ ở bước sau |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
python -m pytest -q
```

- **Kết quả mong đợi:** corruption flow chạy được sau baseline, sinh đủ artifact corrupted/repaired; test suite không bị phá vỡ.
- **Kết quả thực tế:** `run_corruption_flow.py` exit 0 — corrupted hit_rate 0.4, repaired hit_rate 1.0 (bằng baseline); `pytest -q` pass.
- **Artifact/log:** `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn cách chọn record nào bị corrupt trong `corrupt_clean_dataframe()`.
- **Các phương án đã cân nhắc:** (1) chọn ngẫu nhiên bằng `df.sample(..., random_state=...)`; (2) chọn theo slice cố định (theo thứ tự sau khi sort theo `published`/index).
- **Phương án đã chọn:** Slice cố định theo thứ tự index/ngày, không dùng random.
- **Lý do:** Ưu tiên khả năng tái lập (reproducibility) giữa các lần chạy — chạy lại `run_corruption_flow.py` trên cùng baseline luôn cho cùng danh sách `paper_ids` bị corrupt, giúp Linh và Duy đối chiếu số liệu khi review mà không phải cố định seed.
- **Bằng chứng quyết định phù hợp:** Chạy lại `run_corruption_flow.py` nhiều lần trên cùng baseline cho ra cùng danh sách `paper_ids` trong `corruption_log.json` và cùng metric `corrupted_metrics.json`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `NotImplementedError: Student task: implement corruption flow pipeline.` khi chạy `python script/run_corruption_flow.py` trên starter chưa implement.
- **Lệnh hoặc bước tái hiện:** `python script/run_corruption_flow.py` (sau khi đã chạy baseline thành công).
- **Nguyên nhân gốc:** `corruption.py` và `corruption_flow.py` chỉ có pseudo-code + `raise NotImplementedError` theo đúng thiết kế starter (bước 12–14 chưa ai implement).
- **Cách xử lý:** Implement `corrupt_clean_dataframe()` theo đúng 6 gạch đầu dòng trong `Guide.md` (bước 12), sau đó ghép `corruption_flow.py` theo đúng 8 bước trong `Guide.md` (bước 13), giữ nguyên chữ ký hàm mà `script/run_corruption_flow.py` đang gọi.
- **Cách xác minh sau khi sửa:** Chạy lại `run_corruption_flow.py`, không còn lỗi, artifact sinh đầy đủ trong `data/results/` và `data/reports/`.
- **Điều học được:** Trước khi viết orchestration phải đọc kỹ output schema của các hàm đã có sẵn (đặc biệt `evaluate_pipeline()` trả về `EvaluationBundle(summary, answers)`) để không truyền sai kiểu dữ liệu giữa các bước.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?** `crossref.py` gọi REST API, parse thành `PaperRecord`, lưu raw JSON. `cleaning.py` chuẩn hóa, loại record thiếu field, dedupe theo `paper_id`, tính `age_days`, ghép `text_for_embedding`. `LocalEmbeddingIndex.build()` dùng MiniLM để embed rồi nạp vào một collection ChromaDB — với phần của tôi, mỗi trạng thái (corrupted/repaired) có collection riêng (`papers-corrupted`, `papers-repaired`) để không đè lên baseline.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?** `testset.py` sinh câu hỏi từ 5 paper mới nhất, mỗi câu có `ground_truth_doc_ids`. Việc của tôi trong bước 13 là đảm bảo `corruption_flow.py` dùng **lại đúng file** `data/eval/test_set.json` cho cả corrupted và repaired thay vì sinh lại — nếu sinh lại, phép so sánh sẽ mất ý nghĩa vì đổi cả câu hỏi lẫn dữ liệu cùng lúc.
3. **Quality checks khác freshness monitoring ở điểm nào?** Đây là phần Duy triển khai; theo tôi hiểu, quality checks đo tính toàn vẹn cấu trúc tại một thời điểm (null, duplicate, độ dài), còn freshness chỉ đo chiều thời gian (`age_days` so với ngưỡng). Trong `corruption_flow.py` tôi gọi cả hai trên corrupted và repaired dataset để có tín hiệu đầy đủ trước khi kết luận.
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?** Để chênh lệch metric phản ánh đúng ảnh hưởng của thay đổi dữ liệu, không lẫn với việc bộ câu hỏi khác nhau — đây là điều kiện tiên quyết tôi phải giữ khi ghép `corruption_flow.py`.
5. **Repair được xem là thành công dựa trên artifact/metric nào?** `repaired_metrics.json` có 4 chỉ số chính quay lại đúng bằng `baseline_metrics.json` (1.0/1.0/1.0/5.0), và `repaired_quality_report.json`/`repaired_freshness_report.json` (sinh bởi hàm của Duy, tôi chỉ gọi lại) đều pass/fresh trở lại.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.000 | 0.400 | 1.000 | Giảm nhiều nhất — drop 3 record mới nhất + duplicate 2 record làm sai top-k so với `ground_truth_doc_ids` |
| `mean_token_f1` | 1.000 | 0.2947 | 1.000 | Giảm theo do answer bị lấy từ record sai hoặc summary rỗng/nhiễu |
| `judge_accuracy` | 1.000 | 0.2667 | 1.000 | LLM judge đồng thuận với token F1 — phần lớn câu trả lời trên dữ liệu corrupted bị đánh giá sai |
| `mean_judge_score` | 5.000 | 2.5333 | 5.000 | Điểm trung bình giảm hơn một nửa, phục hồi hoàn toàn sau repair |
| Quality checks | pass (7/7) | fail (4/7) | pass (7/7) | Corrupted fail: `paper_id_unique` (duplicate), `title_min_length` (truncate), `summary_min_length` (blank/noise), `freshness_age_days` (stale date) |
| Freshness status | fresh | stale | fresh | `stale_rows` tăng đúng bằng 3 record bị đẩy `published` về 2015 |

### Kết luận từ số liệu

1. **Data corruption** (drop 3 record mới nhất + duplicate 2 row + blank/noise 6 summary + stale date 3 row, theo `corruption_log.json`) → **quality/freshness signal chuyển từ pass/fresh sang fail/stale** (`corrupted_quality_report.json`, `corrupted_freshness_report.json`) → **agent metric giảm mạnh và nhất quán trên cả 4 chỉ số** (`corrupted_metrics.json`: hit_rate 1.0→0.4, judge_accuracy 1.0→0.267).
2. **Repair** (rebuild từ `crossref_records.json`, không sửa trực tiếp corrupted data) → **quality/freshness phục hồi hoàn toàn về pass/fresh** → **agent metric phục hồi hoàn toàn về đúng baseline** (`repaired_metrics.json` = `baseline_metrics.json`).

Corruption ảnh hưởng rõ nhất là tổ hợp **drop latest records + duplicate rows**, vì nó trực tiếp làm sai lệch tập `ground_truth_doc_ids` mà top-k retrieval trả về — kéo `retrieval_hit_rate` giảm mạnh nhất trong 4 metric. Không có kết quả nào khác kỳ vọng ban đầu: corruption có tác động rõ ràng, và repair phục hồi 100% trên toàn bộ metric đo được.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** Corruption ở tầng dữ liệu thuần túy (không đụng code retrieval/LLM) đủ để kéo `retrieval_hit_rate` từ 1.0 xuống 0.4 — chất lượng dữ liệu quan trọng ngang chất lượng model/prompt.
2. **Data quality/observability:** Mỗi loại corruption cần một signal riêng để phát hiện; check tổng quát không bắt hết mọi loại lỗi. Sau khi phát hiện `truncate_title` không bị bộ check ban đầu bắt được, tôi đã bổ sung thêm `title_min_length` (ngưỡng 15 ký tự) vào `run_data_quality_checks()` — nhờ đó `corrupted_quality_report.json` bắt đủ 5/6 loại corruption đã tạo (chỉ `drop_latest_records` không để lại signal trên dữ liệu còn lại, vì bản chất là thiếu dòng chứ không phải dòng sai).
3. **Repair đáng tin cậy:** phải quay về nguồn gốc (raw), không vá lỗi ở tầng dữ liệu đã hỏng — nếu chỉ sửa `corrupted_df` thủ công thì không chứng minh được pipeline có khả năng phục hồi thật sự.

### Nếu có thêm thời gian

Tôi đã bổ sung check `title_min_length` để phát hiện `truncate_title` (xác minh bằng cách so `corrupted_quality_report.json` trước/sau: fail count tăng từ 3/6 lên 4/7 check, `failing=3/21` đúng bằng 3 title bị truncate). Nếu có thêm thời gian, tôi muốn thêm một cảnh báo riêng cho trường hợp `drop_latest_records` — ví dụ so `row_count` của corrupted dataset với baseline để phát hiện dấu hiệu "mất dữ liệu" mà các check hiện tại (vốn chỉ soi từng dòng còn lại) không bắt được.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Tùng Dương
**Ngày xác nhận:** 2026-08-06
