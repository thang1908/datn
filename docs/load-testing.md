# Kiểm thử tải với Locust

Tài liệu này dùng để chạy kiểm thử tải và lấy số liệu đưa vào báo cáo cho hệ thống CS Agent QA.

## Mục tiêu kiểm thử

Chia kiểm thử thành 4 nhóm để kết quả dễ giải thích:

| Scenario | User class | Mục tiêu | Endpoint chính |
| --- | --- | --- | --- |
| API/DB history | `DBHistoryUser` | Đo FastAPI + MongoDB khi đọc danh sách cuộc gọi | `GET /conversations?limit=:limit` |
| Pipeline mock | `PipelineMockUser` | Đo upload audio, SSE và lưu MongoDB nhưng không gọi Gemini | `POST /pipeline/run/mock/stream` |
| Pipeline real | `PipelineUser` | Đo luồng nghiệp vụ thật: upload audio, LangGraph, Gemini, lưu MongoDB | `POST /pipeline/run/stream` |
| Mixed workload | `MixedWorkloadUser` | Mô phỏng người dùng thật: xem lịch sử nhiều hơn upload audio | Cả 2 endpoint trên |

Không dùng `/health`, `/health/ready`, hoặc `/connections/*` làm số liệu tải chính. Các endpoint đó chỉ phù hợp kiểm tra sống/chết hoặc kết nối dịch vụ.

## Chuẩn bị môi trường

1. Chạy MongoDB và backend:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

2. Cài Locust nếu máy chưa có:

```bash
pip install locust
```

3. Chuẩn bị file audio mẫu. Mặc định Locust tự chọn ngẫu nhiên các file `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg` trong thư mục `data/`.

Có thể chỉ định file hoặc thư mục khác:

```bash
export LOCUST_AUDIO_FILE="/path/to/audio.wav"
export LOCUST_AUDIO_DIR="/path/to/audio-folder"
```

Nên ghi lại trong báo cáo: kích thước file, định dạng, độ dài cuộc gọi, model Gemini, cấu hình máy, số worker backend, cấu hình MongoDB, và giá trị `PIPELINE_CONCURRENCY`.

Mock pipeline có thể chỉnh độ trễ giả lập từng node bằng biến môi trường:

```bash
export MOCK_PIPELINE_NODE_DELAY_SECONDS=0.05
```

Endpoint mock bị tắt nếu `APP_ENV=production`.

## Cách chạy lấy số liệu

### 1. Smoke test

Chạy ngắn để chắc backend, MongoDB, Gemini và audio mẫu hoạt động:

```bash
locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 1 -r 1 -t 1m \
  --csv reports/smoke_pipeline \
  --html reports/smoke_pipeline.html \
  PipelineUser
```

Kết quả mong muốn: không có failure, endpoint `/pipeline/run/stream` trả về `result` có `ConversationId`.

### 2. Test API/DB

Chạy tăng dần số user để tìm ngưỡng ổn định của API đọc lịch sử:

```bash
mkdir -p reports

locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 10 -r 5 -t 3m \
  --csv reports/db_10u \
  --html reports/db_10u.html \
  DBHistoryUser

locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 50 -r 10 -t 5m \
  --csv reports/db_50u \
  --html reports/db_50u.html \
  DBHistoryUser

locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 100 -r 10 -t 5m \
  --csv reports/db_100u \
  --html reports/db_100u.html \
  DBHistoryUser
```

Chỉ số cần lấy: RPS, average response time, p50, p95, p99, failure rate.

### 3. Test pipeline mock

Mock pipeline dùng để đo phần backend nội bộ mà không phụ thuộc quota Gemini. Endpoint vẫn nhận file audio, phát SSE progress và lưu kết quả vào MongoDB.

```bash
locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 10 -r 5 -t 3m \
  --csv reports/pipeline_mock_10u \
  --html reports/pipeline_mock_10u.html \
  PipelineMockUser

locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 30 -r 10 -t 5m \
  --csv reports/pipeline_mock_30u \
  --html reports/pipeline_mock_30u.html \
  PipelineMockUser
```

Kết quả này dùng để nhận xét khả năng xử lý upload, SSE, FastAPI và MongoDB khi bỏ giới hạn từ dịch vụ AI bên ngoài.

### 4. Test pipeline thật

Pipeline gọi Gemini thật nên nên chạy từ mức thấp, tránh tạo chi phí và rate limit:

```bash
locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 1 -r 1 -t 3m \
  --csv reports/pipeline_1u \
  --html reports/pipeline_1u.html \
  PipelineUser

locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 3 -r 1 -t 5m \
  --csv reports/pipeline_3u \
  --html reports/pipeline_3u.html \
  PipelineUser

locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 5 -r 1 -t 5m \
  --csv reports/pipeline_5u \
  --html reports/pipeline_5u.html \
  PipelineUser
```

Nếu failure tăng do quota/rate limit Gemini, cần ghi rõ trong báo cáo là giới hạn đến từ dịch vụ AI bên ngoài, không chỉ từ backend.

### 5. Test mixed workload

Scenario này gần với hành vi thật hơn: người dùng xem lịch sử nhiều, thỉnh thoảng upload audio. Tỉ lệ task là 8 phần đọc lịch sử và 2 phần upload, nhưng số request thực tế có thể không đúng 80/20 vì pipeline chạy lâu hơn nhiều.

```bash
locust -f locustfile.py \
  --host http://localhost:8000 \
  --headless -u 20 -r 5 -t 5m \
  --csv reports/mixed_20u \
  --html reports/mixed_20u.html \
  MixedWorkloadUser
```

## Bảng kết quả đưa vào báo cáo

| Scenario | Users | Spawn rate | Duration | Endpoint | RPS | Avg ms | P50 ms | P95 ms | P99 ms | Failure % | Ghi chú |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| API/DB | 10 | 5/s | 3m | `/conversations?limit=:limit` |  |  |  |  |  |  |  |
| API/DB | 50 | 10/s | 5m | `/conversations?limit=:limit` |  |  |  |  |  |  |  |
| Pipeline mock | 10 | 5/s | 3m | `/pipeline/run/mock/stream` |  |  |  |  |  |  | Không gọi Gemini |
| Pipeline mock | 30 | 10/s | 5m | `/pipeline/run/mock/stream` |  |  |  |  |  |  | Không gọi Gemini |
| Pipeline real | 1 | 1/s | 3m | `/pipeline/run/stream` |  |  |  |  |  |  | Gọi Gemini thật |
| Pipeline real | 3 | 1/s | 5m | `/pipeline/run/stream` |  |  |  |  |  |  | Gọi Gemini thật |
| Mixed | 20 | 5/s | 5m | all |  |  |  |  |  |  |  |

Locust sinh các file:

- `*_stats.csv`: số liệu chính theo endpoint.
- `*_failures.csv`: lỗi HTTP, lỗi SSE, lỗi pipeline.
- `*_exceptions.csv`: lỗi runtime phía Locust.
- `*.html`: biểu đồ và bảng tổng hợp để chụp đưa vào phụ lục.

## Cách nhận xét kết quả

Trong báo cáo nên tách kết luận theo từng tầng:

- API/DB ổn định đến bao nhiêu user đồng thời, dựa trên failure rate và p95 latency.
- Pipeline mock xử lý được bao nhiêu request đồng thời khi chỉ đo backend, upload, SSE và MongoDB.
- Pipeline thật xử lý được bao nhiêu request đồng thời trước khi latency tăng mạnh hoặc phát sinh lỗi từ Gemini.
- Nếu lỗi xuất hiện từ Gemini quota/rate limit, ghi rõ đây là giới hạn phụ thuộc nhà cung cấp LLM.
- Với mixed workload, nhận xét trải nghiệm tổng thể: xem lịch sử có bị chậm khi nhiều pipeline đang chạy không.

Mẫu nhận xét khi có kết quả:

> Ở kịch bản pipeline mock, hệ thống đạt ... RPS với p95 ... ms và failure rate ...%, cho thấy phần FastAPI/SSE/MongoDB hoạt động ổn định ở mức ... user đồng thời. Khi chuyển sang pipeline thật, latency tăng lên ... ms và xuất hiện ...% lỗi tại mức ... user. Sự khác biệt này cho thấy nút thắt chính của luồng end-to-end nằm ở thời gian xử lý và giới hạn quota/rate limit của Gemini, không phải riêng phần API nội bộ.

Nếu cả pipeline mock cũng lỗi ở tải thấp, nhận xét nên đổi thành:

> Pipeline mock phát sinh lỗi ngay tại mức ... user, nghĩa là vấn đề nằm trong phần backend nội bộ như upload file, streaming response, MongoDB hoặc tài nguyên máy chủ. Cần tối ưu backend trước khi đánh giá tiếp ảnh hưởng của Gemini.

Ngưỡng chấp nhận có thể dùng cho báo cáo:

- Failure rate dưới 1% với API/DB.
- Failure rate dưới 5% với pipeline end-to-end, nếu có phụ thuộc Gemini thật.
- P95 của `/conversations` không tăng đột biến khi tăng user.
- Pipeline luôn trả về event `result` hợp lệ cho các request thành công.
