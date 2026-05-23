"""Pipeline routes — file upload + SSE streaming + history."""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from src.core.litellm_client import get_langfuse_callback
from src.db import save_conversation
from src.graph.graph import call_graph
from src.utils.constants import get_channel_type

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
    "ConversationId", "ChannelType", "Transcript", "Summary",
    "IsNegative", "NegativeReasonCode", "NegativeReasonDescription",
    "CriteriaScores", "CaseType", "Resolved", "Violations",
]


@router.post("/run/stream")
async def run_pipeline_stream(
    audio: UploadFile = File(..., description="File audio (wav/mp3/m4a/flac)"),
    call_id: str = Form(None, description="Call ID — tự sinh nếu để trống"),
    direction: int = Form(1, description="1 = inbound, 2 = outbound"),
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

    # Sinh call_id nếu không có
    if not call_id:
        call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    conversation_id = f"CALL-{date_str}-{call_id}"

    initial_state = {
        "audio_bytes": audio_bytes,
        "audio_format": audio_format,
        "call_id": call_id,
        "direction": direction,
        "channel_type": get_channel_type(direction),
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
                direction=direction,
            )

            # Gửi kết quả cuối
            yield f"data: {json.dumps({'type': 'result', 'data': output}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Pipeline stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tắt nginx buffering để stream ngay
        },
    )



