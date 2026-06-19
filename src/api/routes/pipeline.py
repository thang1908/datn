"""Pipeline routes — file upload + SSE streaming + history."""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.core.config import settings
from src.core.litellm_client import get_langfuse_callback
from src.db import save_conversation
from src.graph.graph import call_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Map tên node → message hiển thị trên UI
_NODE_MESSAGES = {
    "read_audio":             "📁 Đang đọc file audio...",
    "transcribe_audio":       "🎙️ Đang transcribe audio...",
    "classify_and_resolved":  "🔍 Đang phân loại case...",
    "summarize_conversation": "📝 Đang tóm tắt nội dung...",
    "score_qa":               "📊 Đang chấm điểm QA...",
    "analyze_negative":       "⚠️ Đang phân tích tiêu cực...",
    "merge_output":           "✅ Hoàn thành!",
}

_OUTPUT_KEYS = [
    "ConversationId", "Transcript", "Summary",
    "IsNegative", "NegativeReasonCode", "NegativeReasonDescription",
    "CriteriaScores", "CaseType", "Resolved", "Violations",
]

_MOCK_NODE_DELAY_SECONDS = float(os.getenv("MOCK_PIPELINE_NODE_DELAY_SECONDS", "0.05"))


def _make_conversation_id(call_id: str | None) -> tuple[str, str]:
    if not call_id:
        call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    conversation_id = f"CALL-{date_str}-{call_id}"
    return call_id, conversation_id


def _stream_response(event_generator):
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tắt nginx buffering để stream ngay
        },
    )


def _mock_pipeline_output(conversation_id: str, filename: str, audio_size: int) -> dict:
    return {
        "ConversationId": conversation_id,
        "Transcript": [
            {
                "Speaker": "agent",
                "Text": "Xin chào anh chị, em gọi từ bộ phận chăm sóc khách hàng.",
            },
            {
                "Speaker": "customer",
                "Text": "Tôi cần kiểm tra thông tin dịch vụ hiện tại.",
            },
            {
                "Speaker": "agent",
                "Text": "Em đã tiếp nhận và sẽ hỗ trợ kiểm tra trong hệ thống.",
            },
        ],
        "Summary": (
            "Dữ liệu mock cho kiểm thử tải: hệ thống nhận audio, phát SSE progress, "
            f"tạo kết quả QA và lưu MongoDB. File={filename}, size={audio_size} bytes."
        ),
        "IsNegative": "FALSE",
        "NegativeReasonCode": [],
        "NegativeReasonDescription": [],
        "CriteriaScores": {
            "Communication": 9.0,
            "Attitude": 9.0,
            "DataCollection": 8.5,
            "ProblemSolving": 8.5,
        },
        "CaseType": "MOCK_LOAD_TEST",
        "Resolved": "YES",
        "Violations": [],
    }


@router.post("/run/stream")
async def run_pipeline_stream(
    audio: UploadFile = File(..., description="File audio (wav/mp3/m4a/flac)"),
    call_id: str = Form(None, description="Call ID — tự sinh nếu để trống"),
):
    """
    Upload file audio và nhận kết quả phân tích qua SSE stream.

    Mỗi event SSE có format:
      data: {JSON}\\n\\n

    Các loại event:
    - type=progress: node vừa hoàn thành, kèm message hiển thị
    - type=result:   kết quả phân tích cuối cùng
    - type=error:    có lỗi xảy ra
    """
    # Đọc file
    audio_bytes = await audio.read()
    filename = audio.filename or "audio.wav"
    audio_format = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"

    call_id, conversation_id = _make_conversation_id(call_id)

    initial_state = {
        "audio_bytes": audio_bytes,
        "audio_format": audio_format,
        "call_id": call_id,
        "conversation_id": conversation_id,
    }

    async def event_generator():
        final_state: dict = {}
        completed: list[str] = []

        try:
            cb = get_langfuse_callback()
            cfg = (
                {
                    "callbacks": [cb],
                    "configurable": {"thread_id": conversation_id},
                    "metadata": {"call_id": call_id, "pipeline": "call"},
                }
                if cb else {}
            )

            # Stream từng node — LangGraph emit sau mỗi node xong
            async for chunk in call_graph.astream(initial_state, config=cfg or None):
                node_name = list(chunk.keys())[0]
                completed.append(node_name)
                final_state.update(chunk.get(node_name, {}))

                event = {
                    "type": "progress",
                    "node": node_name,
                    "message": _NODE_MESSAGES.get(node_name, node_name),
                    "completed": completed,
                }
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # Flush Langfuse nếu có
            if cb and hasattr(cb, "flush"):
                try:
                    cb.flush()
                except Exception:
                    pass

            # Build output
            output = {k: final_state.get(k) for k in _OUTPUT_KEYS}
            output["ConversationId"] = conversation_id

            # Lưu vào MongoDB
            await save_conversation(
                message_id=conversation_id,
                crm_output=output,
                call_id=call_id,
            )

            # Gửi kết quả cuối
            yield f"data: {json.dumps({'type': 'result', 'data': output}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Pipeline stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return _stream_response(event_generator)


@router.post("/run/mock/stream")
async def run_pipeline_mock_stream(
    audio: UploadFile = File(..., description="File audio (wav/mp3/m4a/flac)"),
    call_id: str = Form(None, description="Call ID — tự sinh nếu để trống"),
):
    """
    Mock pipeline for load testing without calling Gemini.

    This endpoint keeps the same upload + SSE + MongoDB persistence shape as
    the real pipeline, but returns deterministic QA data. It is disabled in
    production so it is only used for local/staging benchmark reports.
    """
    if settings.is_production:
        raise HTTPException(status_code=404, detail="Mock pipeline is disabled in production")

    audio_bytes = await audio.read()
    filename = audio.filename or "audio.wav"
    call_id, conversation_id = _make_conversation_id(call_id)

    async def event_generator():
        completed: list[str] = []

        try:
            for node_name in _NODE_MESSAGES:
                if _MOCK_NODE_DELAY_SECONDS > 0:
                    await asyncio.sleep(_MOCK_NODE_DELAY_SECONDS)

                completed.append(node_name)
                event = {
                    "type": "progress",
                    "node": node_name,
                    "message": _NODE_MESSAGES.get(node_name, node_name),
                    "completed": completed,
                }
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            output = _mock_pipeline_output(
                conversation_id=conversation_id,
                filename=filename,
                audio_size=len(audio_bytes),
            )
            await save_conversation(
                message_id=conversation_id,
                crm_output=output,
                call_id=call_id,
            )
            yield f"data: {json.dumps({'type': 'result', 'data': output}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Mock pipeline stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return _stream_response(event_generator)

