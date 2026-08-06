# Member Role Report - Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Việt Linh |
| MSSV | 2A202601211 |
| Khóa/Lớp | K3 |
| Tên nhóm | B8 |
| Vai trò chính | Phân công nhóm, chốt clean data schema và đánh giá result test |
| Repository | https://github.com/linhnguyenviet030704-oss/Day10_2A202601211_NguyenVietLinh |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Phân công và điều phối tích hợp | `report/README.md`, quy ước artifact trong repo, thứ tự phụ thuộc giữa các khối | Yêu cầu bài lab, cấu trúc repo, các module phụ thuộc nhau | Phân chia việc theo deliverable, thứ tự tích hợp baseline trước rồi mới corruption/repair | Hoàn thành |
| Chốt clean data schema dùng chung | Review output của `src/ingestion/cleaning.py` và contract mà `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `src/observability/quality.py` dùng | Raw schema từ Crossref, nhu cầu của retrieval/evaluation/quality | Bộ cột clean thống nhất trong `data/clean/papers_clean.csv` và `data/clean/papers_clean.json` | Hoàn thành |
| Đánh giá result test và kết quả pipeline | `data/results/*.json`, `data/quality/*.json`, `data/reports/*.md`, `tests/` | Metrics baseline/corrupted/repaired, quality/freshness report, test command | Kết luận về độ đúng của artifact, chênh lệch metric và trạng thái test trong môi trường phù hợp | Hoàn thành |

Phần việc của tôi thiên về giữ contract chung cho cả nhóm, bảo đảm dữ liệu sạch có schema ổn định để các khối build index, evaluation, quality và reporting không lệch nhau khi tích hợp.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Rà soát output khi ghép pipeline | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Xác minh được baseline, corrupted và repaired đều dùng cùng `data/eval/test_set.json` để so sánh công bằng |
| Kiểm tra report tổng hợp | `src/observability/reporting.py`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Đảm bảo bảng so sánh thể hiện đúng số liệu trong `data/results/` và trạng thái quality/freshness |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Chốt bộ cột clean schema để downstream dùng chung | `src/ingestion/cleaning.py`, `data/clean/papers_clean.csv` | Schema clean gồm các cột: `paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`, `comment`, `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding` | Mở file clean và kiểm tra header; đối chiếu với `_empty_clean_dataframe()` |
| Kiểm tra baseline/corrupted/repaired trên cùng test set | `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json` | Xác nhận baseline và repaired phục hồi về mức 1.0 ở các metric chính, corrupted giảm rõ rệt | Đối chiếu 3 file metrics và `data/reports/corruption_report.md` |
| Đánh giá trạng thái test của repo | `tests/`, `pyproject.toml` | Kết luận test pass trong môi trường đúng chuẩn repo, fail ở môi trường Python 3.14 chạy trực tiếp | Chạy `uv run --with pytest python -m pytest -q` và `python -m pytest -q` |

Artifact quan trọng nhất mà tôi dùng để kết luận là bộ ba metrics trong `data/results/` kết hợp với `data/quality/*.json`. Chúng cho thấy data corruption làm giảm cả retrieval lẫn answer quality, còn repair phục hồi được dataset và metric về baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Nếu nhóm không chốt một clean schema thống nhất từ sớm thì các phần retrieval, evaluation, quality và reporting rất dễ lệch contract. Ví dụ quality cần `age_days`, retrieval cần `text_for_embedding`, còn QA/evaluation cần `paper_id` ổn định để gắn ground-truth document IDs. Vai trò của tôi là khóa bộ cột này để các bạn làm module khác không phải tự suy diễn lại dữ liệu sạch.

### Cách triển khai

Tôi dựa trên output thực tế của `build_clean_dataframe()` để chốt schema clean theo hướng "một dataset đủ dùng cho mọi downstream". Tức là ngoài metadata gốc như `paper_id`, `title`, `summary`, `authors`, `categories`, `published`, nhóm còn giữ thêm các field đã chuẩn hóa sẵn như `authors_joined`, `categories_joined`, `summary_chars`, `age_days` và `text_for_embedding`.

Quyết định này giúp:

- Retrieval/index không phải tự dựng lại text ghép từ nhiều cột.
- Quality/freshness có thể kiểm tra trực tiếp trên `summary`, `paper_id`, `age_days`.
- Evaluation và corruption flow tái sử dụng cùng clean contract mà không cần transform trung gian.
- Repair chỉ cần build lại clean dataframe từ raw records là đủ để phục hồi cả quality lẫn metric.

Ở phần đánh giá result test, tôi tách rõ hai lớp:

1. Kết quả artifact/pipeline.
2. Kết quả test framework theo đúng môi trường.

Khi chạy trực tiếp `python -m pytest -q` trên Python 3.14, test lỗi do import path và tương thích dependency, nên kết quả này không phản ánh lỗi business logic của repo. Khi chuyển sang `uv run --with pytest python -m pytest -q`, repo chạy trên Python 3.13 đúng với `pyproject.toml` và pass `18/18` test. Vì vậy tôi dùng kết quả thứ hai làm căn cứ đánh giá chính thức.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Raw records từ Crossref, cleaned dataset trong `data/clean/`, metrics trong `data/results/`, quality/freshness JSON trong `data/quality/` |
| Output | Kết luận về clean schema dùng chung, kết luận đánh giá baseline/corrupted/repaired, kết luận trạng thái test theo đúng môi trường |
| Module phụ thuộc | `src/ingestion/cleaning.py`, `src/evaluation/testset.py`, `src/observability/quality.py`, `src/retrieval/index.py` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `src/observability/reporting.py` |
| Điều kiện lỗi cần xử lý | Chạy test sai môi trường Python hoặc thiếu `src/` trong import path sẽ cho kết quả fail giả do setup, không phải fail của logic repo |

### Cách xác minh

```bash
uv run --with pytest python -m pytest -q
python -m pytest -q
```

- **Kết quả mong đợi:** Repo pass test khi chạy trong môi trường đúng chuẩn theo `pyproject.toml`, còn nếu dùng runtime không phù hợp thì có thể phát sinh lỗi môi trường.
- **Kết quả thực tế:** `uv run --with pytest python -m pytest -q` pass `18 passed in 7.24s`; `python -m pytest -q` trên Python 3.14 fail trong bước collect/import.
- **Artifact/log:** `data/results/*.json`, `data/quality/*.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Nhóm cần một clean schema vừa đủ cho embedding, evaluation, quality và corruption/repair mà không tạo thêm bước transform phụ.
- **Các phương án đã cân nhắc:** Giữ schema tối giản chỉ gồm metadata gốc; hoặc giữ schema giàu ngữ nghĩa hơn với các field đã chuẩn hóa sẵn cho downstream.
- **Phương án đã chọn:** Dùng clean schema giàu ngữ nghĩa, giữ cả metadata gốc lẫn các field downstream như `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding`.
- **Lý do:** Cách này giảm coupling giữa các module, tránh việc mỗi khối tự build lại field dẫn đến sai khác contract khi tích hợp.
- **Bằng chứng quyết định phù hợp:** `src/observability/quality.py` dùng trực tiếp `paper_id`, `summary`, `age_days`; `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py` chạy end-to-end trên cùng clean dataset; artifact baseline/repaired đạt lại các metric 1.0.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Chạy `python -m pytest -q` ban đầu cho lỗi `ModuleNotFoundError: No module named 'core'`; sau khi thêm `PYTHONPATH=src` thì tiếp tục vướng lỗi dependency trên Python 3.14 như `TypeError: 'function' object is not subscriptable`.
- **Lệnh hoặc bước tái hiện:** `python -m pytest -q` rồi `$env:PYTHONPATH='src'; python -m pytest -q`.
- **Nguyên nhân gốc:** Repo được cấu hình để chạy với Python `>=3.11,<3.14`, nhưng môi trường mặc định đang dùng Python 3.14; ngoài ra chạy trực tiếp không tự cấp đủ context package giống cách `uv` quản lý.
- **Cách xử lý:** Chuyển sang chạy bằng `uv run --with pytest python -m pytest -q` để dùng Python 3.13 và dependency đúng chuẩn repo.
- **Cách xác minh sau khi sửa:** Lệnh `uv run --with pytest python -m pytest -q` pass `18/18`.
- **Điều học được:** Khi đánh giá result test phải tách lỗi môi trường ra khỏi lỗi code; nếu không rất dễ kết luận sai chất lượng bài làm.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. Dữ liệu đi từ Crossref API vào `data/raw/`, sau đó `build_clean_dataframe()` chuẩn hóa thành clean dataset trong `data/clean/`, rồi `LocalEmbeddingIndex.build()` tạo embedding/index để agent truy xuất.
2. Evaluation set chứa `question`, `ground_truth`, `ground_truth_doc_ids`, `question_type`; khi chạy evaluate thì hệ thống so tài liệu truy hồi được và câu trả lời của agent với ground truth để tính hit rate, token F1 và judge score.
3. Quality checks tập trung vào tính hợp lệ/nội dung của dataset như trùng `paper_id`, thiếu `summary`, độ dài `summary`; freshness monitoring tập trung vào độ mới của dữ liệu thông qua `published`, `age_days`, số `stale_rows`.
4. Phải dùng cùng một test set cho baseline, corrupted và repaired thì mới so sánh được tác động của data quality một cách công bằng; nếu đổi câu hỏi hoặc ground truth thì metric không còn cùng mặt bằng nữa.
5. Repair được xem là thành công khi artifact repaired phục hồi lại quality/freshness sang trạng thái pass/fresh và các metric ở `data/results/repaired_metrics.json` quay lại ngang baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.000 | 0.600 | 1.000 | Corruption làm giảm khả năng truy hồi đúng tài liệu; repair phục hồi hoàn toàn |
| `mean_token_f1` | 1.000 | 0.551 | 1.000 | Câu trả lời bị giảm độ khớp rõ khi dữ liệu sạch bị phá |
| `judge_accuracy` | 1.000 | 0.467 | 1.000 | Chất lượng trả lời tổng thể giảm mạnh ở trạng thái corrupted |
| `mean_judge_score` | 5.000 | 2.933 | 5.000 | Điểm đánh giá chủ quan của câu trả lời phản ánh rõ impact của corruption |
| Quality checks | pass | fail | pass | Corrupted fail do duplicate `paper_id`, thiếu `summary`, summary length không hợp lý |
| Freshness status | fresh | stale | fresh | Corrupted có `stale_rows = 1`, repaired về lại trạng thái fresh |

### Kết luận từ số liệu

1. `blank_summary`, `summary_noise`, `duplicate_row`, `stale_publication_date` và việc drop 2 latest records trong `data/results/corruption_log.json` -> quality/freshness chuyển từ `pass/fresh` sang `fail/stale` -> metric agent giảm từ `1.0` xuống `0.6`, `0.551`, `0.467`, `2.933`.
2. Repair bằng cách đọc lại raw records và build lại clean dataframe -> quality/freshness quay lại `pass/fresh` -> metric repaired trở lại đúng bằng baseline ở cả 4 chỉ số chính.

Corruption ảnh hưởng rõ nhất theo tôi là các thay đổi vào `summary` và `paper_id` uniqueness, vì chúng tác động trực tiếp đến cả chất lượng nội dung embedding lẫn khả năng đánh giá/đối chiếu đúng document.

Kết quả đáng chú ý là repaired phục hồi hoàn toàn về baseline thay vì chỉ phục hồi một phần. Điều này cho thấy hướng repair từ raw source đang đúng contract và không chỉ "vá bề mặt" trên corrupted dataset.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data pipeline muốn tích hợp ổn thì phải khóa data contract sớm, nhất là clean schema dùng chung cho nhiều module.
2. Observability không chỉ để báo cáo đẹp mà thực sự giúp nhìn ra nguyên nhân metric RAG giảm, ví dụ duplicate, missing summary và stale rows.
3. Đánh giá chất lượng agent phải gắn với chất lượng dữ liệu; cùng một test set nhưng chỉ cần data corruption là metric có thể giảm mạnh.

### Nếu có thêm thời gian

Tôi muốn bổ sung một bước kiểm tra schema tự động trước khi chạy phase 1 và corruption flow, ví dụ assert đủ các cột bắt buộc như `paper_id`, `summary`, `published`, `age_days`, `text_for_embedding`. Cách đo hiệu quả là giảm lỗi tích hợp do lệch contract và giúp fail sớm trước khi tốn thời gian build index hoặc evaluate.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Việt Linh  
**Ngày xác nhận:** 2026-08-06
