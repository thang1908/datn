"""Node 1: Audio transcription using Gemini multimodal capabilities."""

import base64
import logging

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from src.core.litellm_client import get_lc_config, get_llm
from ..state import CallState
from src.utils.prompts import TRANSCRIBE_PROMPT_TEXT
from src.models.pipeline import TranscribeOutput

logger = logging.getLogger(__name__)


async def transcribe_audio(state: CallState, config: RunnableConfig) -> dict:
    """
    Node 1: Transcribe audio to text using Gemini multimodal.

    Accepts ``audio_bytes`` and ``audio_format``, outputs ``transcript``
    (string) and ``transcript_turns`` (list of speaker/text turns).
    """
    audio_bytes = state["audio_bytes"]
    audio_format = state.get("audio_format", "wav")

    audio_base64 = base64.b64encode(audio_bytes).decode()

    # Gemini multimodal audio format (inline_data)
    mime_type = f"audio/{audio_format}"

    llm = get_llm().with_structured_output(TranscribeOutput)
    message = HumanMessage(
        content=[
            {"type": "text", "text": TRANSCRIBE_PROMPT_TEXT},
            {
                "type": "media",
                "mime_type": mime_type,
                "data": audio_base64,
            },
        ]
    )
    try:
        response = await llm.ainvoke(
            [message],
            config=get_lc_config("transcribe_audio", config),
        )
    except Exception as e:
        logger.error(f"Transcription LLM call failed: {e}", exc_info=True)
        raise

    raw_result = response if isinstance(response, dict) else response.model_dump()

    raw_turns = raw_result.get("transcript")
    transcript_turns = raw_turns if isinstance(raw_turns, list) else []

    transcript = "\n".join(
        f"{turn.get('speaker', '')}: {turn.get('text', '')}"
        for turn in transcript_turns
    )

    return {
        "transcript": transcript,
        "transcript_turns": transcript_turns,
    }
