# BÁO CÁO KỸ THUẬT

## Kiến Trúc Nghiệp Vụ AI — Hệ Thống Phân Tích Cuộc Gọi Tự Động (CS Agent QA)

**Đồ án tốt nghiệp** | Ngày: 06/05/2026
**Sinh viên thực hiện:** Nguyễn Thắng
**Loại hệ thống:** Agentic AI Pipeline — Phân tích chất lượng cuộc gọi CSKH

---

## 1. Tổng Quan Hệ Thống

### 1.1 Mục Tiêu Bài Toán

Trong hoạt động chăm sóc khách hàng (CSKH), việc đánh giá chất lượng cuộc gọi (Quality Assurance — QA) truyền thống đòi hỏi nhân sự nghe lại từng cuộc gọi, ghi nhận vi phạm, và chấm điểm thủ công. Quá trình này tốn nhiều thời gian, dễ bị sai số chủ quan, và không thể mở rộng quy mô.

Đồ án xây dựng hệ thống **CS Agent QA** — một tác nhân AI (AI Agent) hoạt động hoàn toàn tự động nhằm:

- **Nhận diện và phân loại** loại vấn đề của từng cuộc gọi (case type)
- **Đánh giá mức độ giải quyết** vấn đề của nhân viên (resolved / unresolved)
- **Chấm điểm QA** theo bộ tiêu chí đa chiều: Giao tiếp, Thái độ, Thu thập dữ liệu, Giải quyết vấn đề
- **Phát hiện tương tác tiêu cực** và mã hóa nguyên nhân
- **Tóm tắt nội dung** cuộc gọi dưới dạng văn bản có cấu trúc
- **Lưu trữ và quản lý** kết quả phân tích để kiểm tra và hiệu chỉnh thủ công

### 1.2 Phạm Vi Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        CS Agent QA System                       │
│                                                                 │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────────┐  │
│  │  Next.js UI  │◄──►│  FastAPI Server │◄──►│   MongoDB     │  │
│  │  (Dashboard) │    │  (REST + SSE)   │    │  (Storage)    │  │
│  └──────────────┘    └────────┬────────┘    └───────────────┘  │
│                               │                                 │
│                      ┌────────▼────────┐                        │
│                      │  LangGraph AI   │                        │
│                      │  Agent Pipeline │                        │
│                      └────────┬────────┘                        │
│                               │                                 │
│                      ┌────────▼────────┐                        │
│                      │  Google Gemini  │                        │
│                      │  (Multimodal)   │                        │
│                      └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Kiến Trúc Phân Lớp (Layered Architecture)

Hệ thống được tổ chức theo kiến trúc phân lớp rõ ràng, tuân thủ nguyên tắc **Separation of Concerns**:

| Lớp                        | Thư mục           | Trách nhiệm                                 |
| --------------------------- | ------------------- | --------------------------------------------- |
| **Presentation**      | `frontend/`       | Giao diện người dùng Next.js + TypeScript |
| **API Layer**         | `src/api/routes/` | Định nghĩa HTTP endpoints (FastAPI Router) |
| **Service Layer**     | `src/services/`   | Orchestration logic, semaphore concurrency    |
| **Agent/Graph Layer** | `src/graph/`      | LangGraph workflow và các node xử lý AI   |
| **Core**              | `src/core/`       | Config, logging, LLM client                   |
| **Data Layer**        | `src/db/`         | MongoDB async (Motor driver)                  |
| **Models**            | `src/models/`     | Pydantic schemas cho input/output             |

### 2.1 Nguyên Tắc Thiết Kế

- **Single Responsibility**: Mỗi node LangGraph chỉ thực hiện một nhiệm vụ nghiệp vụ duy nhất
- **Dependency Inversion**: Các node phụ thuộc vào interface `CallState`, không phụ thuộc trực tiếp nhau
- **Async-first**: Toàn bộ pipeline chạy bất đồng bộ (Python `asyncio`), tận dụng tối đa I/O-bound LLM calls
- **Structured Output**: Mọi LLM response đều được parse thành Pydantic models để đảm bảo type safety

---

## 3. Kiến Trúc AI Agent — LangGraph Pipeline

### 3.1 Tổng Quan LangGraph

LangGraph là framework xây dựng **Stateful AI Workflows** dưới dạng đồ thị có hướng (Directed Acyclic Graph — DAG). Khác với chuỗi LLM đơn giản (LLMChain), LangGraph cho phép:

- Định nghĩa các **node xử lý** độc lập
- Kiểm soát **luồng dữ liệu** (edges) giữa các node
- Xử lý **song song** nhiều nhánh (fan-out / fan-in)
- Chia sẻ **trạng thái** (state) thống nhất xuyên suốt pipeline

### 3.2 Graph State — Trạng Thái Chung

Toàn bộ pipeline sử dụng một đối tượng trạng thái chung `CallState` (TypedDict), đóng vai trò là **bộ nhớ tạm thời** được truyền qua các node:

```python
class CallState(TypedDict, total=False):
    # Input
    call_id: str | None
    audio_link: str          # URL audio gốc
    direction: int           # 1=inbound, 2=outbound
  
    # Internal
    audio_bytes: bytes       # Nội dung file nhị phân
    audio_format: str        # wav, mp3, m4a, flac
  
    # Node outputs
    transcript: str                      # Văn bản phiên âm
    transcript_turns: list[dict]         # Lượt thoại theo speaker
    case_type: str                       # Phân loại vấn đề
    resolved: Literal["YES","NO","REVIEW"]
    is_negative: Literal["TRUE","FALSE","REVIEW"]
    negative_reason_code: list[str]
    criteria_scores: dict[str, float]    # Điểm từng tiêu chí
    total_score: float
    violations: list[dict]               # Danh sách vi phạm
    summary: str
```

**Ý nghĩa thiết kế**: Bằng cách dùng `TypedDict` với `total=False`, các node chỉ cần đọc/ghi trường mình quan tâm mà không bị ràng buộc thứ tự khởi tạo. LangGraph tự động hợp nhất kết quả từ các nhánh song song.

### 3.3 Sơ Đồ Luồng Pipeline

```
                    ┌─────────────┐
                    │  read_audio │  (Node 0)
                    │  Đọc file   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────────┐
                    │ transcribe_audio │  (Node 1)
                    │ Gemini Multimodal│
                    └──────┬──────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
    ┌─────────▼──────────┐    ┌─────────▼──────────┐
    │ classify_and_       │    │ summarize_          │  (Song song)
    │ resolved            │    │ conversation        │
    │ Phân loại + QĐ      │    │ Tóm tắt nội dung   │
    └─────────┬──────────┘    └─────────┬──────────┘
              │                         │
    ┌─────────┴──────────┐              │
    │                    │              │
  ┌─▼────────┐    ┌──────▼──────┐      │
  │ score_qa │    │ analyze_    │      │  (Song song)
  │ Chấm điểm│    │ negative    │      │
  │ QA       │    │ Tiêu cực    │      │
  └────┬─────┘    └──────┬──────┘      │
       │                 │             │
       └─────────────────┴─────────────┘
                         │
                  ┌──────▼──────┐
                  │ merge_output│
                  │ Hợp nhất kq │
                  └──────┬──────┘
                         │
                       [END]
```

**Phân tích luồng:**

1. **`read_audio`**: Đọc file audio từ URL hoặc upload, xác định định dạng
2. **`transcribe_audio`**: Gửi audio bytes lên Gemini multimodal, nhận transcript có cấu trúc
3. **Fan-out sau transcription**: `classify_and_resolved` và `summarize_conversation` chạy đồng thời
4. **`classify_and_resolved`** → **Fan-out thứ 2**: `score_qa` và `analyze_negative` chạy song song
5. **Fan-in tại `merge_output`**: Tổng hợp kết quả từ tất cả nhánh

### 3.4 Chi Tiết Từng Node

#### Node 1: Phiên Âm Âm Thanh (`transcribe_audio`)

**Công nghệ**: Google Gemini — Multimodal (Audio + Text)

Đây là bước khởi đầu và quan trọng nhất. Node mã hóa file audio dưới dạng Base64 rồi gửi kèm prompt lên Gemini như một **inline multimodal message**:

```python
message = HumanMessage(content=[
    {"type": "text", "text": TRANSCRIBE_PROMPT_TEXT},
    {"type": "media", "mime_type": "audio/wav", "data": audio_base64},
])
llm = get_llm().with_structured_output(TranscribeOutput)
response = await llm.ainvoke([message])
```

**Output có cấu trúc** (`TranscribeOutput`):

```json
{
  "transcript": [
    {"speaker": "agent", "text": "Xin chào, tôi có thể giúp gì cho bạn?"},
    {"speaker": "customer", "text": "Tôi muốn hỏi về đơn hàng 123..."}
  ]
}
```

**Đặc điểm kỹ thuật**: Gemini phân biệt được giọng agent và khách hàng trực tiếp từ audio, không cần xử lý diarization riêng lẻ.

---

#### Node 2a: Phân Loại Vấn Đề (`classify_and_resolved`)

**Công nghệ**: Gemini + LangChain LCEL (structured output)

Node nhận `transcript` và dùng Prompt Template để yêu cầu model phân loại:

- **`case_type`**: Loại vấn đề (khiếu nại, tư vấn, đặt hàng, v.v.)
- **`resolved`**: Mức độ giải quyết — `YES` / `NO` / `REVIEW`

```python
chain = CASE_AND_RESOLVED_PROMPT | llm.with_structured_output(ClassificationResolvedOutput)
result = await chain.ainvoke({"transcript": transcript})
```

**Vai trò trong pipeline**: Kết quả `case_type` và `resolved` được **downstream nodes** (`score_qa`, `analyze_negative`) sử dụng để điều chỉnh tiêu chí đánh giá phù hợp với từng loại case.

---

#### Node 2b: Tóm Tắt Nội Dung (`summarize_conversation`)

**Công nghệ**: Gemini + Prompt có điều kiện (inbound / outbound)

Node chọn prompt khác nhau tùy hướng cuộc gọi:

```python
if direction == DIRECTION_OUTBOUND:
    prompt = SUMMARY_CALL_OUTBOUND_PROMPT
else:
    prompt = SUMMARY_CALL_INBOUND_PROMPT
```

Điều này đảm bảo format tóm tắt phù hợp với ngữ cảnh: cuộc gọi đến từ khách vs. nhân viên chủ động gọi ra.

---

#### Node 3: Phát Hiện Tiêu Cực (`analyze_negative`)

**Công nghệ**: Gemini + Business Rule Logic

Node phân tích cảm xúc và hành vi tiêu cực trong cuộc gọi. Đặc biệt, nó áp dụng **business logic cứng** để đảm bảo nhất quán:

```python
if resolved == "YES":
    is_negative = "FALSE"   # Đã giải quyết → không tiêu cực
elif resolved == "REVIEW":
    is_negative = "REVIEW"  # Cần xem lại → giữ trạng thái REVIEW
else:
    is_negative = "TRUE" if unique_codes else "REVIEW"
```

Output bao gồm:

- `is_negative`: TRUE / FALSE / REVIEW
- `negative_reason_code`: Danh sách mã lý do (e.g., `NEG001`, `NEG002`)
- `negative_reason_description`: Mô tả chi tiết từng mã

---

#### Node 4: Chấm Điểm QA (`score_qa`)

**Công nghệ**: Gemini + Weighted Scoring

Node chấm điểm theo 4 tiêu chí với **trọng số kinh doanh**:

| Tiêu Chí                              | Trọng Số |
| --------------------------------------- | ---------- |
| Giao tiếp (Communication)              | 20%        |
| Thái độ (Attitude)                   | 30%        |
| Thu thập dữ liệu (DataCollection)    | 10%        |
| Giải quyết vấn đề (ProblemSolving) | 40%        |

Ngoài điểm số, model còn trả về danh sách `violations` — các vi phạm cụ thể có trích dẫn câu nói làm bằng chứng:

```json
{
  "ViolationCode": "QA-ATT-01",
  "Description": "Nhân viên ngắt lời khách hàng",
  "Deduction": 1.5,
  "CriterionId": "Attitude",
  "Evidence": [{"Speaker": "agent", "Text": "Vâng nhưng mà..."}]
}
```

---

#### Node 5: Hợp Nhất Kết Quả (`merge_output`)

Node cuối cùng thu thập toàn bộ output từ 3 nhánh hội tụ và định dạng lại theo chuẩn PascalCase để xuất ra API:

```
ConversationId, ChannelType, Transcript, Summary,
IsNegative, NegativeReasonCode, NegativeReasonDescription,
CriteriaScores, CaseType, Resolved, Violations
```

---

## 4. Thiết Kế API

### 4.1 Kiến Trúc REST + SSE

Hệ thống cung cấp API theo hai pattern:

| Pattern              | Endpoint                       | Mô tả                                                           |
| -------------------- | ------------------------------ | ----------------------------------------------------------------- |
| **SSE Stream** | `POST /pipeline/run/stream`  | Upload audio, nhận kết quả từng bước qua Server-Sent Events |
| **REST CRUD**  | `GET /conversations`         | Lấy danh sách kết quả                                         |
| **REST CRUD**  | `GET /conversations/{id}`    | Lấy chi tiết một cuộc gọi                                    |
| **REST CRUD**  | `PATCH /conversations/{id}`  | Cập nhật thủ công (sửa AI nhầm)                             |
| **REST CRUD**  | `DELETE /conversations/{id}` | Xóa bản ghi                                                     |
| **Health**     | `GET /health`                | Kiểm tra trạng thái hệ thống                                 |

### 4.2 SSE Streaming — Cập Nhật Tiến Độ Thực Thời

Pipeline được thiết kế để stream kết quả từng node qua SSE, cho phép UI hiển thị tiến độ xử lý trực quan:

```
Client                              Server (FastAPI)
  |                                      |
  |── POST /pipeline/run/stream ────────►|
  |                                      |── LangGraph bắt đầu
  |◄── data: {type:"progress", node:"read_audio"} ──|
  |◄── data: {type:"progress", node:"transcribe_audio"} |
  |◄── data: {type:"progress", node:"classify_and_resolved"} |
  |◄── data: {type:"progress", node:"score_qa"} ──|
  |◄── data: {type:"progress", node:"analyze_negative"} |
  |◄── data: {type:"progress", node:"merge_output"} |
  |◄── data: {type:"result", data:{...full output...}} |
```

**Kỹ thuật thực hiện**: FastAPI `StreamingResponse` + LangGraph `astream()` — mỗi node hoàn thành sẽ emit một chunk, server chuyển ngay thành SSE event mà không chờ pipeline kết thúc.

### 4.3 Kiểm Soát Đồng Thời

```python
_semaphore = asyncio.Semaphore(settings.pipeline_concurrency)

async with _get_semaphore():
    result = await call_graph.ainvoke(initial_state)
```

`Semaphore` giới hạn số pipeline chạy đồng thời, tránh quá tải API Gemini và đảm bảo latency ổn định.

---

## 5. Công Nghệ Sử Dụng

### 5.1 Backend Stack

| Công Nghệ                      | Phiên Bản | Vai Trò                                |
| -------------------------------- | ----------- | --------------------------------------- |
| **Python**                 | 3.11+       | Ngôn ngữ chính                       |
| **FastAPI**                | 0.136.1     | Web framework async, OpenAPI tự động |
| **Uvicorn**                | 0.46.0      | ASGI server                             |
| **LangGraph**              | 1.1.10      | AI workflow orchestration               |
| **LangChain**              | 1.2.16      | LLM abstraction layer                   |
| **langchain-google-genai** | 4.2.2       | Gemini API integration                  |
| **Google Gemini**          | Flash Lite  | Multimodal LLM (audio + text)           |
| **Pydantic**               | 2.13.3      | Data validation + structured output     |
| **Motor**                  | 3.7.1       | MongoDB async driver                    |
| **Langfuse**               | 4.5.1       | LLM observability & tracing             |
| **httpx**                  | 0.28.1      | Async HTTP client                       |
| **Docker**                 | —          | Containerization                        |

### 5.2 Frontend Stack

| Công Nghệ                     | Vai Trò                     |
| ------------------------------- | ---------------------------- |
| **Next.js 14**            | React framework (App Router) |
| **TypeScript**            | Type safety                  |
| **Tailwind CSS**          | Utility-first styling        |
| **SSE / EventSource API** | Nhận stream từ backend     |

### 5.3 Infrastructure

| Thành Phần            | Công Nghệ                                  |
| ----------------------- | -------------------------------------------- |
| **Database**      | MongoDB (local-first)                        |
| **Container**     | Docker + Docker Compose                      |
| **Observability** | Langfuse (LLM tracing, latency, token usage) |

---

## 6. Thiết Kế Frontend

### 6.1 Luồng Người Dùng

```
Upload audio file
      │
      ▼
Progress Bar (SSE updates)
  - Đang đọc file audio...
  - Đang transcribe audio...
  - Đang phân loại case...
  - Đang tóm tắt...
  - Đang chấm điểm QA...
  - Đang phân tích tiêu cực...
  - Hoàn thành!
      │
      ▼
Result Dashboard
  ┌──────────┬──────────┬──────────┬──────────┐
  │Case Type │ Resolved │ Negative │ QA Score │
  └──────────┴──────────┴──────────┴──────────┘
  ┌─────────────────────┬─────────────────────┐
  │  Điểm QA Chi Tiết   │  Tóm Tắt Nội Dung  │
  │  (Progress bars)    │  (Text + Neg codes) │
  └─────────────────────┴─────────────────────┘
  ┌───────────────────────────────────────────┐
  │         Transcript Cuộc Gọi              │
  │     (Chat-style, agent vs. customer)      │
  └───────────────────────────────────────────┘
  ┌───────────────────────────────────────────┐
  │      Vi Phạm (Violations)                │
  │  Code | Description | Deduction | Evidence│
  └───────────────────────────────────────────┘
```

### 6.2 Quản Lý Lịch Sử

Dashboard lịch sử hỗ trợ:

- **Xem danh sách** các cuộc gọi đã phân tích (phân trang)
- **Xem chi tiết** từng kết quả
- **Sửa thủ công** (PATCH) các trường AI có thể nhầm: CaseType, Resolved, IsNegative, Summary
- **Xóa** bản ghi không cần thiết (DELETE)

---

## 7. Observability — Giám Sát Hệ Thống AI

Hệ thống tích hợp **Langfuse** để theo dõi toàn bộ vòng đời của mỗi LLM call:

```python
langfuse_callback = get_langfuse_callback()
config = {
    "callbacks": [langfuse_callback],
    "configurable": {"thread_id": conversation_id},
    "metadata": {"call_id": call_id, "pipeline": "call"},
}
result = await call_graph.ainvoke(initial_state, config=config)
```

**Thông tin được trace**:

- Latency từng node
- Số token input/output mỗi LLM call
- Prompt được gửi đi
- Raw response từ model
- Metadata cuộc gọi (call_id, pipeline name)

---

## 8. Bảo Mật và Cấu Hình

Toàn bộ thông tin nhạy cảm được quản lý qua **Environment Variables** với `pydantic-settings`:

| Biến Môi Trường      | Mô Tả                                  |
| ------------------------ | ---------------------------------------- |
| `GEMINI_API_KEY`       | Google AI API key                        |
| `MONGODB_URI`          | Connection string MongoDB                |
| `LANGFUSE_PUBLIC_KEY`  | Observability key (tùy chọn)           |
| `PIPELINE_CONCURRENCY` | Số pipeline tối đa chạy đồng thời |
| `MAX_UPLOAD_BYTES`     | Giới hạn kích thước file upload     |

CORS được cấu hình cho phép chỉ frontend local (`localhost:3000`) trong môi trường development.

---

## 9. Ưu Điểm Kiến Trúc

### 9.1 Xử Lý Song Song Hiệu Quả

Pipeline tận dụng tính năng fan-out của LangGraph để chạy đồng thời:

- `classify_and_resolved` + `summarize_conversation` (sau transcription)
- `score_qa` + `analyze_negative` (sau classification)

Điều này giúp giảm latency tổng thể so với xử lý tuần tự.

### 9.2 Extensibility (Khả Năng Mở Rộng)

Kiến trúc node-based cho phép dễ dàng:

- Thêm node mới vào pipeline (ví dụ: sentiment analysis chi tiết hơn)
- Thay đổi LLM model (chỉ cần sửa `litellm_client.py`)
- Điều chỉnh luồng dữ liệu mà không ảnh hưởng các node khác

### 9.3 Auditability (Khả Năng Kiểm Tra)

- Kết quả AI được lưu vào MongoDB kèm timestamp
- Cho phép nhân viên QA sửa lại kết quả sai (PATCH endpoint)
- Langfuse trace toàn bộ LLM calls để debug
# DATN
